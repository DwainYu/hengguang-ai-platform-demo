"""Unit tests for the safety incident analysis tool (synthetic data, fixed operations)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.agent.tools.safety import SafetyIncidentAnalysisTool
from app.auth.permissions import Permission
from app.db.database import Database

ALLOWED_OPERATIONS = (
    "incident_by_area",
    "incident_by_severity",
    "incident_by_category",
    "recent_high_risk",
    "incident_trend",
)


@pytest.fixture
def tool(seeded_database: Database) -> SafetyIncidentAnalysisTool:
    return SafetyIncidentAnalysisTool(seeded_database)


class TestToolContract:
    def test_identity_and_permission(self):
        assert SafetyIncidentAnalysisTool.name == "safety_incident_analysis"
        assert SafetyIncidentAnalysisTool.permission == Permission.TOOL_SAFETY

    def test_operations_are_the_fixed_whitelist(self, tool):
        assert set(tool.operations) == set(ALLOWED_OPERATIONS)

    def test_high_risk_operation_uses_the_shared_severity_definition(self, tool):
        from app.db.queries import HIGH_RISK_SEVERITIES

        assert HIGH_RISK_SEVERITIES == ("high", "critical")
        assert tool.operations["recent_high_risk"].params == ("days", "limit", "area")

    def test_no_free_form_query_argument(self, tool):
        assert set(tool.parameters["properties"]) == {"operation", "days", "limit", "area"}


class TestArgumentValidation:
    def test_days_bounds(self):
        with pytest.raises(ValidationError):
            SafetyIncidentAnalysisTool.args_model.model_validate(
                {"operation": "incident_trend", "days": 400}
            )

    def test_unknown_operation(self):
        with pytest.raises(ValidationError):
            SafetyIncidentAnalysisTool.args_model.model_validate({"operation": "incident_delete"})

    def test_area_length_bound(self):
        with pytest.raises(ValidationError):
            SafetyIncidentAnalysisTool.args_model.model_validate(
                {"operation": "incident_by_area", "area": "x" * 60}
            )


@pytest.mark.asyncio
class TestOperations:
    async def test_incident_by_area_ranks_areas(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "incident_by_area", "days": 30, "limit": 5})
        )
        assert result.success, result.error
        rows = result.metadata["payload"]["data"]
        assert rows, "expected synthetic incidents inside the window"
        counts = [row["incidents"] for row in rows]
        assert counts == sorted(counts, reverse=True)
        assert {"area", "incidents", "high_risk", "unresolved", "share_pct"} <= set(rows[0])

    async def test_incident_by_severity_is_ordered_most_severe_first(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "incident_by_severity", "days": 120})
        )
        severities = [row["severity"] for row in result.metadata["payload"]["data"]]
        order = ["critical", "high", "medium", "low"]
        assert severities == sorted(severities, key=order.index)

    async def test_recent_high_risk_only_returns_high_or_critical(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "recent_high_risk", "days": 120, "limit": 20})
        )
        rows = result.metadata["payload"]["data"]
        assert rows
        assert {row["severity"] for row in rows} <= {"high", "critical"}
        dates = [row["created_at"] for row in rows]
        assert dates == sorted(dates, reverse=True)

    async def test_incident_trend_buckets_are_inside_the_window(self, tool):
        result = await tool.execute(tool.validate({"operation": "incident_trend", "days": 30}))
        rows = result.metadata["payload"]["data"]
        assert rows
        starts = [row["period_start"] for row in rows]
        assert starts == sorted(starts)
        assert all(date.fromisoformat(row["period_end"]) for row in rows)

    async def test_incident_by_category_totals(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "incident_by_category", "days": 120})
        )
        rows = result.metadata["payload"]["data"]
        assert rows
        assert all(row["incidents"] >= row["high_risk"] >= 0 for row in rows)

    async def test_area_filter_narrows_high_risk_rows(self, tool):
        top = (
            await tool.execute(
                tool.validate({"operation": "incident_by_area", "days": 120, "limit": 1})
            )
        ).metadata["payload"]["data"][0]
        result = await tool.execute(
            tool.validate(
                {"operation": "recent_high_risk", "days": 120, "limit": 10, "area": top["area"]}
            )
        )
        assert result.success
        for row in result.metadata["payload"]["data"]:
            assert row["area"] == top["area"]

    async def test_content_mentions_dataset_and_synthetic_source(self, tool):
        result = await tool.execute(tool.validate({"operation": "incident_by_area", "days": 30}))
        assert "【安全事件数据】" in result.content
        assert "data/synthetic" in result.content

    async def test_unknown_area_returns_no_rows_not_an_error(self, tool):
        result = await tool.execute(
            tool.validate({"operation": "recent_high_risk", "days": 30, "area": "不存在区"})
        )
        assert result.success is True
        assert result.metadata["payload"]["data"] == []

    async def test_unknown_operation_is_contained(self, tool):
        result = await tool.execute({"operation": "incident_exfiltrate", "days": 30})
        assert result.success is False
        assert result.error_code == "INVALID_OPERATION"

    async def test_broken_database_is_contained(self, tmp_path):
        broken = Database(url=f"sqlite:///{tmp_path / 'broken.db'}")
        broken.initialize()
        with broken.session() as session:
            session.execute(text("DROP TABLE safety_incidents"))
        tool = SafetyIncidentAnalysisTool(broken)
        result = await tool.execute(tool.validate({"operation": "incident_by_area", "days": 30}))
        assert result.success is False
        assert result.error_code
