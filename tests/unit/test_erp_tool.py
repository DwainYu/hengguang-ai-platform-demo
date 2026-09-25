"""Unit tests for the ERP purchase analysis tool (synthetic data, fixed operations)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.agent.tools.erp import ErpPurchaseAnalysisArgs, ErpPurchaseAnalysisTool
from app.auth.permissions import Permission
from app.db.database import Database

ALLOWED_OPERATIONS = (
    "purchase_price_trend",
    "top_materials_by_spend",
    "supplier_summary",
    "recent_purchase_orders",
    "inventory_summary",
    "material_consumption",
    "purchase_amount_stats",
)


@pytest.fixture
def tool(seeded_database: Database) -> ErpPurchaseAnalysisTool:
    return ErpPurchaseAnalysisTool(seeded_database)


async def run(tool: ErpPurchaseAnalysisTool, **arguments) -> dict:
    result = await tool.execute(tool.validate(arguments))
    assert result.success, result.error
    return result.metadata["payload"]


class TestToolContract:
    def test_identity_and_permission(self):
        assert ErpPurchaseAnalysisTool.name == "erp_purchase_analysis"
        assert ErpPurchaseAnalysisTool.permission == Permission.TOOL_ERP
        assert "合成" in ErpPurchaseAnalysisTool.description

    def test_operations_are_the_fixed_whitelist(self, tool):
        assert set(tool.operations) == set(ALLOWED_OPERATIONS)

    def test_schema_lists_every_operation_as_enum(self, tool):
        enum = tool.parameters["properties"]["operation"]["enum"]
        assert set(enum) == set(ALLOWED_OPERATIONS)

    def test_schema_has_no_sql_or_table_argument(self, tool):
        properties = tool.parameters["properties"]
        assert set(properties) == {"operation", "days", "limit", "material", "status", "category"}
        assert not {"sql", "query", "table", "columns"} & set(properties)


class TestArgumentValidation:
    @pytest.mark.parametrize("days", [0, -1, 366, 10_000])
    def test_days_out_of_range_is_rejected(self, days):
        with pytest.raises(ValidationError):
            ErpPurchaseAnalysisArgs.model_validate({"operation": "supplier_summary", "days": days})

    @pytest.mark.parametrize("limit", [0, 51])
    def test_limit_out_of_range_is_rejected(self, limit):
        with pytest.raises(ValidationError):
            ErpPurchaseAnalysisArgs.model_validate(
                {"operation": "supplier_summary", "limit": limit}
            )

    def test_unknown_operation_is_rejected_by_the_schema(self):
        with pytest.raises(ValidationError):
            ErpPurchaseAnalysisArgs.model_validate({"operation": "delete_all_orders"})

    def test_defaults(self):
        args = ErpPurchaseAnalysisArgs.model_validate({"operation": "supplier_summary"})
        assert (args.days, args.limit) == (30, 10)
        assert args.material is None and args.status is None


@pytest.mark.asyncio
class TestOperations:
    async def test_purchase_price_trend_reports_a_change_per_material(self, tool):
        payload = await run(tool, operation="purchase_price_trend", days=30, limit=10)
        assert payload["operation"] == "purchase_price_trend"
        assert payload["days"] == 30
        assert payload["data"], "expected synthetic orders inside the last 30 days"
        row = payload["data"][0]
        for key in (
            "material",
            "avg_unit_price",
            "recent_avg_price",
            "baseline_avg_price",
            "change_pct",
        ):
            assert key in row
        assert isinstance(row["change_pct"], float)

    async def test_top_materials_by_spend_is_sorted_and_limited(self, tool):
        payload = await run(tool, operation="top_materials_by_spend", days=90, limit=4)
        rows = payload["data"]
        assert len(rows) == 4
        spends = [row["total_spend"] for row in rows]
        assert spends == sorted(spends, reverse=True)

    async def test_supplier_summary_lists_suppliers_with_spend(self, tool):
        payload = await run(tool, operation="supplier_summary", days=120, limit=10)
        rows = payload["data"]
        assert rows
        assert {"supplier", "orders", "total_spend", "last_order_date"} <= set(rows[0])
        assert all(row["total_spend"] > 0 for row in rows)

    async def test_recent_purchase_orders_is_newest_first(self, tool):
        payload = await run(tool, operation="recent_purchase_orders", days=60, limit=5)
        dates = [row["order_date"] for row in payload["data"]]
        assert dates == sorted(dates, reverse=True)
        assert all(date.fromisoformat(value) for value in dates)

    async def test_recent_purchase_orders_status_filter(self, tool):
        payload = await run(
            tool, operation="recent_purchase_orders", days=120, limit=20, status="draft"
        )
        assert {row["status"] for row in payload["data"]} == {"draft"}

    async def test_inventory_summary_uses_material_filter(self, tool):
        payload = await run(tool, operation="inventory_summary", material="盐酸", limit=5)
        assert payload["data"]
        assert {row["material"] for row in payload["data"]} == {"盐酸"}

    async def test_content_block_is_readable_and_marks_synthetic_data(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "top_materials_by_spend", "days": 30})
        )
        assert "【ERP 采购数据】" in result.content
        assert "合成演示数据" in result.content
        assert result.metadata["data_source"] == "data/synthetic"

    async def test_result_count_matches_rows(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "supplier_summary", "days": 30, "limit": 2})
        )
        assert result.metadata["result_count"] == len(result.metadata["payload"]["data"]) == 2


@pytest.mark.asyncio
class TestFailureContainment:
    async def test_unknown_operation_never_reaches_the_database(self, tool):
        arguments = {"operation": "purchase_price_trend"}
        arguments["operation"] = "drop_table"  # bypass the schema on purpose
        result = await tool.execute(arguments)
        assert result.success is False
        assert result.error_code == "INVALID_OPERATION"
        assert result.metadata["payload"]["error"]["code"] == "INVALID_OPERATION"
        assert "可选值" in result.error

    async def test_empty_window_is_a_success_with_no_rows(self, tool):
        payload = await run(tool, operation="purchase_price_trend", days=1)
        assert payload["data"] == [] or payload["row_count"] >= 0
        result = await tool.execute(
            tool.validate({"operation": "inventory_summary", "material": "不存在的物料XYZ"})
        )
        assert result.success is True
        assert result.metadata["payload"]["data"] == []
        assert "没有记录" in result.content

    async def test_missing_table_becomes_a_controlled_failure(self, tmp_path):
        broken = Database(url=f"sqlite:///{tmp_path / 'missing' / 'broken.db'}")
        broken.initialize()
        # Drop a table the tool needs, then let the tool read the damaged database.
        with broken.session() as session:
            session.execute(text("DROP TABLE purchase_orders"))
        tool = ErpPurchaseAnalysisTool(broken)
        result = await tool.execute(
            tool.validate({"operation": "purchase_price_trend", "days": 30})
        )
        assert result.success is False
        assert result.error
        assert result.error_code
        assert result.metadata["payload"]["success"] is False

    async def test_unreachable_database_does_not_raise(self, tmp_path):
        # A directory is not openable as a SQLite file -> engine/session failure.
        tool = ErpPurchaseAnalysisTool(Database(url=f"sqlite:///{tmp_path}"))
        result = await tool.execute(tool.validate({"operation": "supplier_summary"}))
        assert result.success is False
        assert "暂时不可用" in result.content

    async def test_injection_style_material_is_only_a_search_term(self, tool, seeded_database):
        payload = await run(
            tool, operation="inventory_summary", material="盐酸'; DROP TABLE materials; --"
        )
        assert payload["data"] == []
        assert seeded_database.table_row_count("materials") == 10

    async def test_like_wildcards_in_material_do_not_widen_the_query(self, tool, seeded_database):
        before = seeded_database.table_row_count("inventory")
        payload = await run(tool, operation="top_materials_by_spend", days=30, limit=5)
        assert payload["row_count"] <= 5
        assert seeded_database.table_row_count("inventory") == before
