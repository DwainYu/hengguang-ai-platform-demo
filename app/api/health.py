"""GET /health — liveness probe (public, no token; SPEC keeps it free of business data)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.db.database import get_database
from app.db.models import Base
from app.observability.metrics import metrics
from app.observability.middleware import request_id_of

router = APIRouter(tags=["health"])

RequestIdDep = Annotated[str, Depends(request_id_of)]


@router.get("/health")
def health(request_id: RequestIdDep) -> dict:
    """Status, version and a cheap database probe."""

    database = get_database()
    business_tables = ("suppliers", "materials", "purchase_orders", "safety_incidents")
    rows: dict[str, int] = {}
    if database.is_initialized:
        rows = {table: database.table_row_count(table) for table in business_tables}
    return {
        "status": "ok",
        "version": get_settings().app_version,
        "database": {
            "configured": bool(database.url),
            "initialized": database.is_initialized,
            "tables": len(Base.metadata.tables),
            "seeded": bool(rows) and all(rows.values()),
            "rows": rows,
        },
        "request_count": metrics.snapshot()["request_count"],
        "request_id": request_id,
    }
