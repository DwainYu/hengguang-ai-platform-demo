"""Safety incident analysis tool — fixed operations over ``safety_incidents``.

Same contract as the ERP tool: no real DCS / safety-system connection, only the
four whitelisted operations, Pydantic-validated arguments and fixed parameterized
queries against the synthetic dataset in ``data/synthetic``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.agent.tools.business import BusinessOperation, BusinessQueryTool
from app.auth.permissions import Permission
from app.db import queries

SafetyOperation = Literal[
    "incident_by_area",
    "incident_by_severity",
    "incident_by_category",
    "recent_high_risk",
    "incident_trend",
]


class SafetyIncidentAnalysisArgs(BaseModel):
    """Validated arguments for ``safety_incident_analysis``."""

    operation: SafetyOperation = Field(
        description=(
            "Fixed safety operation: incident_by_area (which area reports most), "
            "incident_by_severity, incident_by_category, recent_high_risk, incident_trend."
        )
    )
    days: int = Field(
        default=30, ge=1, le=365, description="Analysis window in days, counted back from today."
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max rows to return.")
    area: str | None = Field(
        default=None, min_length=1, max_length=40, description="Optional area filter."
    )


class SafetyIncidentAnalysisTool(BusinessQueryTool):
    """Read-only safety incident analysis (synthetic data, fixed queries only)."""

    name = "safety_incident_analysis"
    permission = Permission.TOOL_SAFETY
    dataset_label = "安全事件数据"
    description = (
        "查询合成安全生产事件数据。operation 只能是 incident_by_area / incident_by_severity / "
        "incident_by_category / recent_high_risk / incident_trend；数据全部为演示用合成数据。"
    )
    args_model = SafetyIncidentAnalysisArgs
    operations = {
        "incident_by_area": BusinessOperation(
            name="incident_by_area",
            description="按区域统计事件数量与高风险数量",
            query=queries.incident_by_area,
            params=("days", "limit"),
            columns=("area", "incidents", "high_risk", "unresolved", "share_pct"),
        ),
        "incident_by_severity": BusinessOperation(
            name="incident_by_severity",
            description="按严重程度统计事件",
            query=queries.incident_by_severity,
            params=("days",),
            columns=("severity", "incidents", "unresolved", "areas"),
        ),
        "incident_by_category": BusinessOperation(
            name="incident_by_category",
            description="按隐患类别统计事件",
            query=queries.incident_by_category,
            params=("days", "limit"),
            columns=("category", "incidents", "high_risk"),
        ),
        "recent_high_risk": BusinessOperation(
            name="recent_high_risk",
            description="最近的高风险/重大风险事件明细",
            query=queries.recent_high_risk,
            params=("days", "limit", "area"),
            columns=("created_at", "area", "category", "severity", "status"),
        ),
        "incident_trend": BusinessOperation(
            name="incident_trend",
            description="按周分桶的事件趋势",
            query=queries.incident_trend,
            params=("days",),
            columns=("period_start", "period_end", "incidents", "high_risk", "unresolved"),
        ),
    }


__all__ = ["SafetyIncidentAnalysisArgs", "SafetyIncidentAnalysisTool", "SafetyOperation"]
