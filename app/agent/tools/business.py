"""Shared plumbing for the ERP / safety business tools (Day 4).

Both tools are *fixed-operation* query tools: the model picks one whitelisted
``operation`` per call, the tool maps it onto a fixed parameterized SQL function in
:mod:`app.db.queries`, and returns two views of the same result:

* ``content`` — a readable text block for the model (and the mock provider),
* ``metadata["payload"]`` — the ``{"success", "operation", "days", "data"}``
  structure the platform API, audit trail and Day-5 dashboard consume.

The base class owns the repetitive parts (database access, parameter passing,
empty results, failure containment), so a new business tool is just an args model
plus an operation map.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.agent.tools.base import Tool, ToolResult
from app.api.errors import ERROR_DATABASE
from app.db.database import Database, get_database
from app.db.queries import BusinessQueryError

logger = logging.getLogger("app.agent.tools.business")

#: Rows rendered into the model-facing text block (payload keeps them all).
MAX_CONTENT_ROWS = 8

#: Chinese labels for the text block. The structured payload keeps the SQL column
#: names so the Day-5 dashboard can bind table columns programmatically.
COLUMN_LABELS = {
    "material": "物料",
    "category": "品类",
    "unit": "单位",
    "spec": "规格",
    "supplier": "供应商",
    "supplier_code": "供应商编码",
    "rating": "评级",
    "active": "合作中",
    "orders": "订单数",
    "purchase_orders": "采购订单数",
    "qty": "数量",
    "quantity": "数量",
    "avg_unit_price": "均价",
    "amount": "金额",
    "total_spend": "采购金额",
    "total_amount": "采购金额",
    "total_qty": "总数量",
    "first_half_avg": "前半段均价",
    "second_half_avg": "后半段均价",
    "change_pct": "变化率%",
    "trend": "趋势",
    "order_no": "单号",
    "order_date": "日期",
    "unit_price": "单价",
    "status": "状态",
    "warehouse": "仓库",
    "current_qty": "当前库存",
    "safety_qty": "安全库存",
    "below_safety": "低于安全库存",
    "week": "周",
    "total_quantity": "总数量",
    "consumed_qty": "消耗量",
    "avg_monthly_qty": "月均量",
    "materials": "物料数",
    "material_count": "物料数",
    "supplier_status": "供应商状态",
    "suppliers": "供应商数",
    "avg_order_amount": "平均订单金额",
    "measure": "口径",
    "first_order_date": "首单日期",
    "last_order_date": "最近订单",
    "updated_at": "更新时间",
    "incidents": "事件数",
    "total_incidents": "事件总数",
    "high_risk": "高风险数",
    "unresolved": "未闭环数",
    "share_pct": "占比%",
    "severity": "严重度",
    "area": "区域",
    "incident_date": "日期",
    "incident_no": "事件编号",
    "title": "标题",
    "description": "描述",
    "closed": "已闭环",
    "count": "数量",
    "days": "天数",
    "window_start": "窗口起始",
    "window_end": "窗口结束",
    "equipment": "设备",
    "baseline_price": "基准单价",
}

DatabaseProvider = Callable[[], Database]


@dataclass(frozen=True)
class BusinessOperation:
    """One fixed query operation exposed to the model."""

    name: str
    description: str
    query: Callable[..., Any]
    #: Which validated tool arguments are forwarded to the query function.
    params: tuple[str, ...] = ("days",)
    #: Columns rendered in the text block (defaults to every column of the row).
    columns: tuple[str, ...] = ()

    def run(self, session: Any, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """Call the fixed query with only the parameters it declares."""

        result = self.query(session, **{key: arguments[key] for key in self.params})
        if isinstance(result, dict):
            return [result]
        return list(result)


def _constant_provider(database: Database) -> DatabaseProvider:
    def provider() -> Database:
        return database

    return provider


class BusinessQueryTool(Tool):
    """Base class for fixed-operation business tools (ERP, safety, ...)."""

    #: Heading used in the text block, e.g. "ERP 采购数据".
    dataset_label: str = "业务数据"
    #: operation name → operation definition (set by subclasses).
    operations: dict[str, BusinessOperation] = {}

    def __init__(self, database: Database | DatabaseProvider | None = None) -> None:
        if database is None:
            self._database: DatabaseProvider = get_database
        elif isinstance(database, Database):
            self._database = _constant_provider(database)
        else:
            self._database = database

    @property
    def operation_names(self) -> tuple[str, ...]:
        return tuple(self.operations)

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """Run one fixed operation; every failure path stays controlled."""

        operation_name = str(arguments.get("operation", ""))
        operation = self.operations.get(operation_name)
        if operation is None:
            return self._failure(
                f"不支持的 operation '{operation_name}'，可选值：{', '.join(self.operations)}",
                code="INVALID_OPERATION",
                operation=operation_name,
            )

        days = int(arguments.get("days") or 0)
        try:
            with self._database().session() as session:
                rows = operation.run(session, arguments)
        except BusinessQueryError as error:
            return self._failure(str(error), code=ERROR_DATABASE, operation=operation_name)
        except Exception as error:  # noqa: BLE001 — never let a tool crash the agent
            logger.warning(
                "business tool query failed",
                extra={
                    "event": "tool.error",
                    "tool": self.name,
                    "error_type": type(error).__name__,
                },
            )
            return self._failure(
                f"{self.dataset_label}暂时不可用（{type(error).__name__}）",
                code=ERROR_DATABASE,
                operation=operation_name,
            )

        payload = {
            "success": True,
            "operation": operation_name,
            "dataset": self.dataset_label,
            "data_source": "data/synthetic",
            "days": days,
            "row_count": len(rows),
            "data": rows,
            "disclaimer": "合成演示数据（synthetic demo data），非真实企业数据。",
        }
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=self.render(operation, arguments, rows),
            metadata={
                "operation": operation_name,
                "days": days,
                "result_count": len(rows),
                "data_source": "data/synthetic",
                "payload": payload,
            },
        )

    def _failure(self, message: str, *, code: str, operation: str) -> ToolResult:
        payload: dict[str, Any] = {
            "success": False,
            "operation": operation,
            "dataset": self.dataset_label,
            "data_source": "data/synthetic",
            "days": 0,
            "data": [],
            "error": {"code": code, "message": message},
        }
        return ToolResult(
            tool_name=self.name,
            success=False,
            content=f"数据查询失败：{message}",
            metadata={"operation": operation, "result_count": 0, "payload": payload},
            error=message,
            error_code=code,
        )

    def render(
        self,
        operation: BusinessOperation,
        arguments: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> str:
        """Readable text block for the model (and for the mock provider's answer)."""

        header = (
            f"【{self.dataset_label}】operation={operation.name} "
            f"days={arguments.get('days')} rows={len(rows)}"
        )
        if not rows:
            return f"{header}\n该时间窗口内没有记录（合成演示数据）。"

        columns = operation.columns or tuple(rows[0].keys())
        lines = [header]
        for index, row in enumerate(rows[:MAX_CONTENT_ROWS], start=1):
            parts = [
                f"{COLUMN_LABELS.get(column, column)}={_fmt(row[column])}"
                for column in columns
                if column in row
            ]
            lines.append(f"{index}. " + ", ".join(parts))
        if len(rows) > MAX_CONTENT_ROWS:
            lines.append(f"...（共 {len(rows)} 行，仅展示前 {MAX_CONTENT_ROWS} 行）")
        lines.append("数据来源：data/synthetic 合成演示数据，非真实企业数据。")
        return "\n".join(lines)


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.2f}"
        return f"{value:.2f}".rstrip("0").rstrip(".")
    text = str(value)
    return text if len(text) <= 80 else text[:77] + "..."


__all__ = ["MAX_CONTENT_ROWS", "BusinessOperation", "BusinessQueryTool", "DatabaseProvider"]
