"""ERP purchase analysis tool — fixed operations over the synthetic ERP tables.

The demo has **no real ERP connection**: every number comes from the local SQLite
database seeded from ``data/synthetic`` (see :mod:`app.db.seed`). Only the seven
operations below can run; there is no way to pass SQL, a table name or a column
name through this tool — arguments are validated by Pydantic and bound as
parameters to fixed queries in :mod:`app.db.queries`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.agent.tools.business import BusinessOperation, BusinessQueryTool
from app.auth.permissions import Permission
from app.db import queries

ErpOperation = Literal[
    "purchase_price_trend",
    "top_materials_by_spend",
    "supplier_summary",
    "recent_purchase_orders",
    "inventory_summary",
    "material_consumption",
    "purchase_amount_stats",
]

ErpCategory = Literal["化工原料", "辅料", "能源"]

OrderStatus = Literal["received", "in_transit", "settled", "draft"]


class ErpPurchaseAnalysisArgs(BaseModel):
    """Validated arguments for ``erp_purchase_analysis``."""

    operation: ErpOperation = Field(
        description=(
            "Fixed ERP operation: purchase_price_trend (price change inside the window), "
            "top_materials_by_spend, supplier_summary, recent_purchase_orders, inventory_summary, "
            "material_consumption, purchase_amount_stats."
        )
    )
    days: int = Field(
        default=30, ge=1, le=365, description="Analysis window in days, counted back from today."
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max rows to return.")
    material: str | None = Field(
        default=None, min_length=1, max_length=40, description="Optional material name filter."
    )
    status: OrderStatus | None = Field(
        default=None, description="Optional purchase order status filter."
    )
    category: ErpCategory | None = Field(
        default=None, description="Optional material category filter (purchase_amount_stats)."
    )


class ErpPurchaseAnalysisTool(BusinessQueryTool):
    """Read-only ERP purchase analysis (synthetic data, fixed queries only)."""

    name = "erp_purchase_analysis"
    permission = Permission.TOOL_ERP
    dataset_label = "ERP 采购数据"
    description = (
        "查询合成 ERP 采购数据（供应商、物料、采购订单、库存）。operation 只能是 "
        "purchase_price_trend / top_materials_by_spend / supplier_summary / "
        "recent_purchase_orders / inventory_summary / material_consumption / "
        "purchase_amount_stats；数据全部为演示用合成数据。"
    )
    args_model = ErpPurchaseAnalysisArgs
    operations = {
        "purchase_price_trend": BusinessOperation(
            name="purchase_price_trend",
            description="平均采购单价与前后半段价格变化",
            query=queries.purchase_price_trend,
            params=("days", "material", "limit"),
            columns=("material", "unit", "orders", "avg_unit_price", "change_pct", "total_spend"),
        ),
        "top_materials_by_spend": BusinessOperation(
            name="top_materials_by_spend",
            description="按采购金额排名的主要物料",
            query=queries.top_materials_by_spend,
            params=("days", "limit"),
            columns=("material", "category", "orders", "total_quantity", "unit", "total_spend"),
        ),
        "supplier_summary": BusinessOperation(
            name="supplier_summary",
            description="按采购金额排名的供应商",
            query=queries.supplier_summary,
            params=("days", "limit"),
            columns=(
                "supplier",
                "orders",
                "materials",
                "total_spend",
                "last_order_date",
                "supplier_status",
            ),
        ),
        "recent_purchase_orders": BusinessOperation(
            name="recent_purchase_orders",
            description="窗口内最近的采购订单",
            query=queries.recent_purchase_orders,
            params=("days", "limit", "status"),
            columns=(
                "order_date",
                "material",
                "quantity",
                "unit",
                "unit_price",
                "supplier",
                "status",
            ),
        ),
        "inventory_summary": BusinessOperation(
            name="inventory_summary",
            description="当前库存（快照，不受 days 影响）",
            query=queries.inventory_summary,
            params=("material", "limit"),
            columns=("material", "warehouse", "quantity", "unit", "updated_at"),
        ),
        "material_consumption": BusinessOperation(
            name="material_consumption",
            description="窗口内物料消耗量（以采购量为口径）",
            query=queries.material_consumption,
            params=("days", "material", "limit"),
            columns=(
                "material",
                "category",
                "unit",
                "orders",
                "consumed_qty",
                "avg_monthly_qty",
                "avg_unit_price",
            ),
        ),
        "purchase_amount_stats": BusinessOperation(
            name="purchase_amount_stats",
            description="按品类的采购金额统计",
            query=queries.purchase_amount_stats,
            params=("days", "category"),
            columns=(
                "category",
                "orders",
                "total_spend",
                "avg_order_amount",
                "suppliers",
                "share_pct",
            ),
        ),
    }


__all__ = ["ErpPurchaseAnalysisArgs", "ErpPurchaseAnalysisTool"]
