"""Fixed, parameterized business queries over the synthetic ERP / safety tables.

Every function in this module is a *fixed operation*: the SQL text is a module
constant and only values are bound as parameters. There is no path from a tool
argument to SQL syntax, so a question such as ``"; DROP TABLE materials; --"``
is treated as a literal search term (the demo ERP database is synthetic anyway,
but the isolation is what a real ERP adapter would need).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger("app.db.queries")

#: Statuses counted as "high risk" by the safety tools.
HIGH_RISK_SEVERITIES = ("high", "critical")


class BusinessQueryError(RuntimeError):
    """A fixed business query failed (missing table, broken data, unusable DB ...)."""


_PURCHASE_PRICE_TREND_SQL = """
SELECT
    m.name                          AS material,
    m.unit                          AS unit,
    m.category                      AS category,
    COUNT(*)                        AS orders,
    ROUND(AVG(po.unit_price), 2)    AS avg_unit_price,
    ROUND(MIN(po.unit_price), 2)    AS min_unit_price,
    ROUND(MAX(po.unit_price), 2)    AS max_unit_price,
    ROUND(
        AVG(CASE WHEN po.order_date >= :mid_date THEN po.unit_price END), 2
    ) AS recent_avg_price,
    ROUND(
        AVG(CASE WHEN po.order_date < :mid_date THEN po.unit_price END), 2
    ) AS baseline_avg_price,
    ROUND(SUM(po.quantity * po.unit_price), 2) AS total_spend
FROM purchase_orders po
JOIN materials m ON m.id = po.material_id
WHERE po.order_date >= :cutoff
  AND (:material IS NULL OR m.name LIKE :material_like)
GROUP BY m.id, m.name, m.unit, m.category
ORDER BY total_spend DESC
LIMIT :limit
"""

_TOP_MATERIALS_BY_SPEND_SQL = """
SELECT
    m.name                                   AS material,
    m.unit                                   AS unit,
    m.category                               AS category,
    COUNT(*)                                 AS orders,
    ROUND(SUM(po.quantity), 2)               AS total_quantity,
    ROUND(SUM(po.quantity * po.unit_price), 2) AS total_spend,
    ROUND(AVG(po.unit_price), 2)             AS avg_unit_price
FROM purchase_orders po
JOIN materials m ON m.id = po.material_id
WHERE po.order_date >= :cutoff
GROUP BY m.id, m.name, m.unit, m.category
ORDER BY total_spend DESC
LIMIT :limit
"""

_SUPPLIER_SUMMARY_SQL = """
SELECT
    s.name                                        AS supplier,
    s.category                                    AS supplier_category,
    s.region                                      AS region,
    s.status                                      AS supplier_status,
    COUNT(po.id)                                  AS orders,
    COUNT(DISTINCT m.id)                          AS materials,
    ROUND(SUM(po.quantity * po.unit_price), 2)    AS total_spend,
    MAX(po.order_date)                            AS last_order_date
FROM purchase_orders po
JOIN suppliers s ON s.id = po.supplier_id
JOIN materials m ON m.id = po.material_id
WHERE po.order_date >= :cutoff
GROUP BY s.id, s.name, s.category, s.region, s.status
ORDER BY total_spend DESC
LIMIT :limit
"""

_RECENT_PURCHASE_ORDERS_SQL = """
SELECT
    po.id                                        AS order_id,
    po.order_date                                AS order_date,
    s.name                                       AS supplier,
    m.name                                       AS material,
    po.quantity                                  AS quantity,
    m.unit                                       AS unit,
    po.unit_price                                AS unit_price,
    ROUND(po.quantity * po.unit_price, 2)        AS amount,
    po.status                                    AS status
FROM purchase_orders po
JOIN suppliers s ON s.id = po.supplier_id
JOIN materials m ON m.id = po.material_id
WHERE po.order_date >= :cutoff
  AND (:status IS NULL OR po.status = :status)
ORDER BY po.order_date DESC, po.id DESC
LIMIT :limit
"""

_INVENTORY_SUMMARY_SQL = """
SELECT
    i.warehouse                        AS warehouse,
    m.name                             AS material,
    m.unit                             AS unit,
    ROUND(i.quantity, 2)               AS quantity,
    i.updated_at                       AS updated_at
FROM inventory i
JOIN materials m ON m.id = i.material_id
WHERE (:material IS NULL OR m.name LIKE :material_like)
ORDER BY i.quantity DESC
LIMIT :limit
"""

_MATERIAL_CONSUMPTION_SQL = """
SELECT
    m.name                                              AS material,
    m.category                                          AS category,
    m.unit                                              AS unit,
    COUNT(po.id)                                        AS orders,
    ROUND(COALESCE(SUM(po.quantity), 0), 2)             AS consumed_qty,
    ROUND(COALESCE(SUM(po.quantity), 0) / :months, 2)   AS avg_monthly_qty,
    ROUND(COALESCE(SUM(po.quantity * po.unit_price), 0), 2) AS total_amount,
    ROUND(COALESCE(AVG(po.unit_price), 0), 2)           AS avg_unit_price
FROM materials m
LEFT JOIN purchase_orders po
    ON po.material_id = m.id AND po.order_date >= :cutoff
WHERE (:material IS NULL OR m.name LIKE :material_like)
GROUP BY m.id, m.name, m.category, m.unit
HAVING COALESCE(SUM(po.quantity), 0) > 0
ORDER BY consumed_qty DESC
LIMIT :limit
"""

_PURCHASE_AMOUNT_STATS_SQL = """
SELECT
    m.category                                       AS category,
    COUNT(po.id)                                     AS orders,
    ROUND(COALESCE(SUM(po.quantity * po.unit_price), 0), 2)   AS total_spend,
    ROUND(COALESCE(AVG(po.quantity * po.unit_price), 0), 2)   AS avg_order_amount,
    COUNT(DISTINCT po.supplier_id)                   AS suppliers,
    MIN(po.order_date)                               AS first_order_date,
    MAX(po.order_date)                               AS last_order_date
FROM purchase_orders po
JOIN materials m ON m.id = po.material_id
WHERE po.order_date >= :cutoff
    AND (:category IS NULL OR m.category = :category)
GROUP BY m.category
ORDER BY total_spend DESC
"""

_INCIDENT_BY_AREA_SQL = """
SELECT
    si.area                                                              AS area,
    COUNT(*)                                                             AS incidents,
    SUM(CASE WHEN si.severity IN ('high', 'critical') THEN 1 ELSE 0 END) AS high_risk,
    SUM(CASE WHEN si.status <> 'closed' THEN 1 ELSE 0 END)               AS unresolved,
    MIN(si.created_at)                                                   AS first_reported_at,
    MAX(si.created_at)                                                   AS latest_reported_at
FROM safety_incidents si
WHERE si.created_at >= :cutoff
GROUP BY si.area
ORDER BY incidents DESC, area ASC
LIMIT :limit
"""

_INCIDENT_WINDOW_TOTAL_SQL = """
SELECT
    COUNT(*)                                                              AS incidents,
    SUM(CASE WHEN si.severity IN ('high', 'critical') THEN 1 ELSE 0 END)  AS high_risk,
    SUM(CASE WHEN si.status <> 'closed' THEN 1 ELSE 0 END)                AS unresolved
FROM safety_incidents si
WHERE si.created_at >= :cutoff
"""

_INCIDENT_BY_SEVERITY_SQL = """
SELECT
    si.severity                              AS severity,
    COUNT(*)                                 AS incidents,
    SUM(CASE WHEN si.status <> 'closed' THEN 1 ELSE 0 END) AS unresolved,
    COUNT(DISTINCT si.area)                  AS areas
FROM safety_incidents si
WHERE si.created_at >= :cutoff
GROUP BY si.severity
ORDER BY incidents DESC
"""

_INCIDENT_BY_CATEGORY_SQL = """
SELECT
    si.category                              AS category,
    COUNT(*)                                 AS incidents,
    SUM(CASE WHEN si.severity IN ('high', 'critical') THEN 1 ELSE 0 END) AS high_risk
FROM safety_incidents si
WHERE si.created_at >= :cutoff
GROUP BY si.category
ORDER BY incidents DESC
LIMIT :limit
"""

_RECENT_HIGH_RISK_SQL = """
SELECT
    si.id               AS incident_id,
    si.created_at       AS created_at,
    si.area             AS area,
    si.category         AS category,
    si.severity         AS severity,
    si.status           AS status,
    si.description      AS description
FROM safety_incidents si
WHERE si.created_at >= :cutoff
  AND si.severity IN ('high', 'critical')
  AND (:area IS NULL OR si.area = :area)
ORDER BY si.created_at DESC, si.id DESC
LIMIT :limit
"""

_INCIDENT_TREND_SQL = """
SELECT
    CAST((julianday(substr(si.created_at, 1, 10)) - julianday(:cutoff)) / 7 AS INTEGER) AS bucket,
    MIN(substr(si.created_at, 1, 10))            AS period_start,
    MAX(substr(si.created_at, 1, 10))            AS period_end,
    COUNT(*)                                     AS incidents,
    SUM(CASE WHEN si.severity IN ('high', 'critical') THEN 1 ELSE 0 END) AS high_risk,
    SUM(CASE WHEN si.status <> 'closed' THEN 1 ELSE 0 END)               AS unresolved
FROM safety_incidents si
WHERE si.created_at >= :cutoff
GROUP BY bucket
ORDER BY bucket ASC
"""


def cutoff_date(days: int, *, anchor: date | None = None) -> date:
    """Inclusive start date of the ``days``-day analysis window ending today."""

    return (anchor or date.today()) - timedelta(days=days - 1)


def _midpoint(cutoff: date, days: int) -> str:
    return (cutoff + timedelta(days=max(1, days // 2))).isoformat()


def _run(session: Session, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        rows = session.execute(text(sql), params).mappings().all()
    except SQLAlchemyError as exc:  # pragma: no cover - depends on a broken database
        logger.warning(
            "business query failed",
            extra={
                "event": "db.query_error",
                "error_type": exc.__class__.__name__,
                "error": str(exc)[:200],
            },
        )
        raise BusinessQueryError(f"业务数据查询失败：{exc.__class__.__name__}") from exc
    return [dict(row) for row in rows]


def _pct(change: float | None) -> float | None:
    return None if change is None else round(change * 100, 2)


def _with_spend_share(rows: list[dict[str, Any]], *, spend_key: str) -> list[dict[str, Any]]:
    """Add ``share_pct`` of total spend to grouped rows."""

    window_spend = sum(row.get(spend_key) or 0 for row in rows)
    for row in rows:
        row["share_pct"] = _pct((row.get(spend_key) or 0) / window_spend) if window_spend else None
    return rows


def _with_change_percent(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add ``change_pct`` from the recent/baseline averages of a price window."""

    for row in rows:
        recent = row.get("recent_avg_price")
        baseline = row.get("baseline_avg_price")
        if recent and baseline:
            row["change_pct"] = _pct(recent / baseline - 1.0)
        else:
            row["change_pct"] = None
    return rows


# --------------------------------------------------------------------------- ERP


def purchase_price_trend(
    session: Session,
    *,
    days: int,
    material: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Average purchase price per material in the window, with first/second half change."""

    start = cutoff_date(days)
    rows = _run(
        session,
        _PURCHASE_PRICE_TREND_SQL,
        {
            "cutoff": start.isoformat(),
            "mid_date": _midpoint(start, days),
            "material": material,
            "material_like": f"%{material}%" if material else None,
            "limit": limit,
        },
    )
    return _with_change_percent(rows)


def top_materials_by_spend(session: Session, *, days: int, limit: int = 10) -> list[dict[str, Any]]:
    """Materials ranked by purchase spend inside the window."""

    return _run(
        session,
        _TOP_MATERIALS_BY_SPEND_SQL,
        {"cutoff": cutoff_date(days).isoformat(), "limit": limit},
    )


def supplier_summary(session: Session, *, days: int, limit: int = 10) -> list[dict[str, Any]]:
    """Suppliers ranked by purchase spend inside the window."""

    return _run(
        session,
        _SUPPLIER_SUMMARY_SQL,
        {"cutoff": cutoff_date(days).isoformat(), "limit": limit},
    )


def recent_purchase_orders(
    session: Session,
    *,
    days: int,
    limit: int = 10,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Most recent purchase orders inside the window (newest first)."""

    return _run(
        session,
        _RECENT_PURCHASE_ORDERS_SQL,
        {"cutoff": cutoff_date(days).isoformat(), "status": status, "limit": limit},
    )


def inventory_summary(
    session: Session, *, material: str | None = None, limit: int = 10
) -> list[dict[str, Any]]:
    """Current synthetic warehouse stock, largest quantity first."""

    return _run(
        session,
        _INVENTORY_SUMMARY_SQL,
        {
            "material": material,
            "material_like": f"%{material}%" if material else None,
            "limit": limit,
        },
    )


def material_consumption(
    session: Session, *, days: int, material: str | None = None, limit: int = 10
) -> list[dict[str, Any]]:
    """Material usage inside the window.

    Consumption proxy: the synthetic model has no separate usage ledger, so purchased
    quantity is used, clearly labelled for the demo.
    """

    start = cutoff_date(days).isoformat()
    rows = _run(
        session,
        _MATERIAL_CONSUMPTION_SQL,
        {
            "cutoff": start,
            "months": max(round(days / 30.0, 2), 1.0),
            "material": material,
            "material_like": f"%{material}%" if material else None,
            "limit": limit,
        },
    )
    for row in rows:
        row["measure"] = "purchased_quantity"
    return rows


def purchase_amount_stats(
    session: Session, *, days: int, category: str | None = None
) -> list[dict[str, Any]]:
    """Spend totals and order statistics grouped by material category."""

    rows = _run(
        session,
        _PURCHASE_AMOUNT_STATS_SQL,
        {"cutoff": cutoff_date(days).isoformat(), "category": category},
    )
    return _with_spend_share(rows, spend_key="total_spend")


# ------------------------------------------------------------------------ Safety


def incident_by_area(session: Session, *, days: int, limit: int = 10) -> list[dict[str, Any]]:
    """Safety incidents per area (with high-risk and unresolved counts + share)."""

    start = cutoff_date(days).isoformat()
    rows = _run(session, _INCIDENT_BY_AREA_SQL, {"cutoff": start, "limit": limit})
    total = _run(session, _INCIDENT_WINDOW_TOTAL_SQL, {"cutoff": start})
    window_incidents = (total[0].get("incidents") if total else 0) or 0
    for row in rows:
        row["share_pct"] = _pct(row["incidents"] / window_incidents) if window_incidents else None
    return rows


def incident_window_summary(session: Session, *, days: int) -> dict[str, Any]:
    """Totals for the window: incidents, high risk, unresolved."""

    rows = _run(session, _INCIDENT_WINDOW_TOTAL_SQL, {"cutoff": cutoff_date(days).isoformat()})
    if not rows:
        return {"incidents": 0, "high_risk": 0, "unresolved": 0}
    return {key: (value or 0) for key, value in rows[0].items()}


def incident_by_severity(session: Session, *, days: int) -> list[dict[str, Any]]:
    """Safety incidents per severity level, most severe first."""

    rows = _run(session, _INCIDENT_BY_SEVERITY_SQL, {"cutoff": cutoff_date(days).isoformat()})
    order = {name: index for index, name in enumerate(("critical", "high", "medium", "low"))}
    rows.sort(key=lambda row: order.get(row["severity"], len(order)))
    return rows


def incident_by_category(session: Session, *, days: int, limit: int = 10) -> list[dict[str, Any]]:
    """Safety incidents per cause category."""

    return _run(
        session,
        _INCIDENT_BY_CATEGORY_SQL,
        {"cutoff": cutoff_date(days).isoformat(), "limit": limit},
    )


def recent_high_risk(
    session: Session,
    *,
    days: int,
    limit: int = 10,
    area: str | None = None,
) -> list[dict[str, Any]]:
    """Recent high/critical safety incidents inside the window (newest first)."""

    return _run(
        session,
        _RECENT_HIGH_RISK_SQL,
        {"cutoff": cutoff_date(days).isoformat(), "area": area, "limit": limit},
    )


def incident_trend(session: Session, *, days: int) -> list[dict[str, Any]]:
    """Weekly incident buckets across the window (oldest bucket first)."""

    return _run(session, _INCIDENT_TREND_SQL, {"cutoff": cutoff_date(days).isoformat()})


__all__ = [
    "HIGH_RISK_SEVERITIES",
    "BusinessQueryError",
    "cutoff_date",
    "incident_by_area",
    "incident_by_category",
    "incident_by_severity",
    "incident_trend",
    "incident_window_summary",
    "inventory_summary",
    "purchase_price_trend",
    "recent_high_risk",
    "recent_purchase_orders",
    "supplier_summary",
    "top_materials_by_spend",
]
