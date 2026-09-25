"""Deterministic seeding of the synthetic ERP / safety database.

``data/synthetic/seed.json`` holds the *catalogue* data (demo users, suppliers,
materials, warehouses, safety classifications) plus the parameters used to
materialise the time-series tables (``purchase_orders``, ``safety_incidents``).

Time-series rows are generated relative to an anchor date so that "the last 30
days" always contains data on the day the demo runs. Generation is fully
deterministic: the same anchor date and the same ``meta.random_seed`` always
produce identical rows, which keeps the demo repeatable and the tests stable.
Nothing in here is real enterprise data.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from collections.abc import Callable, Iterator
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings, update_settings
from app.db.database import Database, get_database
from app.db.models import (
    Equipment,
    Inventory,
    MaintenanceRecord,
    Material,
    PurchaseOrder,
    SafetyIncident,
    Supplier,
    User,
)

logger = logging.getLogger("app.db.seed")

SEED_FILENAME = "seed.json"

#: Tables the business tools query; they must never be empty after seeding.
BUSINESS_TABLES = ("suppliers", "materials", "purchase_orders", "inventory", "safety_incidents")


class SeedValidationError(ValueError):
    """The synthetic seed file is inconsistent (unknown ids, bad weights, ranges ...)."""


def load_seed(path: Path | None = None) -> dict[str, Any]:
    """Read the synthetic seed file."""

    seed_path = (
        Path(path) if path is not None else Path(get_settings().synthetic_dir) / SEED_FILENAME
    )
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SeedValidationError(f"{seed_path} must contain a JSON object")
    return payload


def _options(rows: list[dict[str, Any]], label: str) -> list[tuple[str, int]]:
    options = [(str(row.get("value", row.get("name"))), int(row["weight"])) for row in rows]
    if not options or any(weight <= 0 for _value, weight in options):
        raise SeedValidationError(f"{label}: entries must have positive weights")
    return options


def validate_seed(payload: dict[str, Any]) -> None:
    """Validate the seed file before anything touches the database."""

    meta = payload["meta"]
    if int(meta["days_back"]) < 14:
        raise SeedValidationError("meta.days_back must cover at least two weeks of history")

    materials = payload.get("materials", [])
    suppliers = payload.get("suppliers", [])
    if not materials or not suppliers:
        raise SeedValidationError("seed.json must define at least one supplier and one material")

    material_ids = {int(row["id"]) for row in materials}
    supplier_ids = {int(row["id"]) for row in suppliers}
    for table in ("suppliers", "materials"):
        ids = [int(row["id"]) for row in payload.get(table, [])]
        if len(ids) != len(set(ids)):
            raise SeedValidationError(f"table '{table}' has duplicate ids")

    preferred = payload.get("supplier_preferred_material_ids", {})
    for key, linked in preferred.items():
        supplier_id = int(key)
        if supplier_id not in supplier_ids:
            raise SeedValidationError(
                f"supplier_preferred_material_ids references unknown supplier {supplier_id}"
            )
        if not linked:
            raise SeedValidationError(f"supplier {supplier_id} must list at least one material")
        for material_id in linked:
            if int(material_id) not in material_ids:
                raise SeedValidationError(
                    f"supplier {supplier_id} references unknown material {material_id}"
                )

    for row in payload.get("inventory", []):
        if int(row["material_id"]) not in material_ids:
            raise SeedValidationError(f"inventory references unknown material {row['material_id']}")

    safety = payload["safety"]
    categories = {str(row["name"]) for row in safety["categories"]}
    described = set(safety.get("descriptions", {}))
    if described - categories:
        raise SeedValidationError(
            f"safety.descriptions has unknown categories: {sorted(described - categories)}"
        )
    if categories - described:
        raise SeedValidationError(
            f"safety.descriptions is missing: {sorted(categories - described)}"
        )

    order_options = payload["purchase_order_options"]
    _options(order_options["statuses"], "purchase_order_options.statuses")
    low, high = (float(value) for value in order_options["quantity_range"])
    if not 0 < low <= high:
        raise SeedValidationError(
            "purchase_order_options.quantity_range must be an increasing positive range"
        )
    for group in ("areas", "categories", "severities", "statuses"):
        _options(safety[group], f"safety.{group}")


def _pick(rng: random.Random, options: list[tuple[str, int]]) -> str:
    return rng.choices(
        [value for value, _ in options], weights=[weight for _, weight in options], k=1
    )[0]


def _weeks(days_back: int, per_week: int) -> Iterator[tuple[int, int]]:
    """Yield ``(week_index, occurrences_in_week)`` covering ``days_back`` days.

    Week 0 is the partial week containing the anchor date, so a longer history
    only prepends older weeks: the recent rows the demo queries stay put.
    """

    total_weeks = max(1, round(days_back / 7))
    remainder = days_back - (total_weeks - 1) * 7
    for index in range(total_weeks):
        yield index, remainder if index == 0 else per_week


def _slot_date(anchor: date, week_index: int, rng: random.Random, days_back: int) -> date:
    age = min(week_index * 7 + rng.randint(0, 6), days_back - 1)
    return anchor - timedelta(days=age)


def generate_purchase_orders(payload: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    """Deterministically generate synthetic purchase orders ending at ``as_of``."""

    meta = payload["meta"]
    days_back = int(meta["days_back"])
    materials = {int(row["id"]): row for row in payload["materials"]}
    preferred = {
        int(sid): [int(mid) for mid in ids]
        for sid, ids in payload["supplier_preferred_material_ids"].items()
    }
    options = payload["purchase_order_options"]
    statuses = _options(options["statuses"], "purchase_order_options.statuses")
    quantity_min, quantity_max = (float(value) for value in options["quantity_range"])
    price_round = int(meta.get("unit_price_round", 2))
    quantity_round = int(meta.get("quantity_round", 2))

    cycle = [
        (supplier_id, material_id)
        for supplier_id, ids in sorted(preferred.items())
        for material_id in ids
    ]

    rows: list[dict[str, Any]] = []
    cursor = 0
    for week_index, occurrences in _weeks(days_back, int(meta["purchase_orders_per_week"])):
        for slot in range(1, occurrences + 1):
            supplier_id, material_id = cycle[cursor % len(cycle)]
            cursor += 1
            rng = random.Random(f"{meta['random_seed']}:po:{week_index}:{slot}:{material_id}")
            material = materials[material_id]
            order_date = _slot_date(as_of, week_index, rng, days_back)
            days_since_start = max(0, days_back - (as_of - order_date).days)
            drift = 1.0 + float(material["drift_per_day"]) * days_since_start
            noise = rng.uniform(-1.0, 1.0) * float(material["volatility"])
            rows.append(
                {
                    "supplier_id": supplier_id,
                    "material_id": material_id,
                    "quantity": round(rng.uniform(quantity_min, quantity_max), quantity_round),
                    "unit_price": round(
                        max(0.01, float(material["base_price"]) * (drift + noise)), price_round
                    ),
                    "order_date": order_date.isoformat(),
                    "status": _pick(rng, statuses),
                }
            )
    rows.sort(key=lambda row: (row["order_date"], row["material_id"], row["supplier_id"]))
    return rows


def generate_safety_incidents(payload: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    """Deterministically generate synthetic safety incidents ending at ``as_of``."""

    meta = payload["meta"]
    safety = payload["safety"]
    days_back = int(meta["days_back"])
    areas = _options(safety["areas"], "safety.areas")
    categories = _options(safety["categories"], "safety.categories")
    severities = _options(safety["severities"], "safety.severities")
    statuses = _options(safety["statuses"], "safety.statuses")
    descriptions = safety["descriptions"]

    rows: list[dict[str, Any]] = []
    for week_index, occurrences in _weeks(days_back, int(meta["safety_incidents_per_week"])):
        for slot in range(1, occurrences + 1):
            rng = random.Random(f"{meta['random_seed']}:si:{week_index}:{slot}")
            area = _pick(rng, areas)
            category = _pick(rng, categories)
            incident_date = _slot_date(as_of, week_index, rng, days_back)
            created_at = datetime.combine(incident_date, datetime.min.time()) + timedelta(
                hours=rng.randint(7, 21), minutes=rng.randint(0, 59)
            )
            rows.append(
                {
                    "area": area,
                    "category": category,
                    "severity": _pick(rng, severities),
                    "status": _pick(rng, statuses),
                    "description": f"[{area}] {rng.choice(descriptions[category])}（合成示例）",
                    "created_at": created_at.isoformat(sep=" ", timespec="minutes"),
                }
            )
    rows.sort(key=lambda row: (row["created_at"], row["area"]))
    return rows


def generate_inventory(payload: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    """Materialise warehouse stock rows with timestamps relative to ``as_of``."""

    rows = []
    for entry in payload.get("inventory", []):
        updated_at = datetime.combine(
            as_of - timedelta(days=int(entry.get("updated_days_ago", 0))),
            datetime.min.time(),
        ) + timedelta(hours=8, minutes=30)
        rows.append(
            {
                "material_id": int(entry["material_id"]),
                "warehouse": str(entry["warehouse"]),
                "quantity": float(entry["quantity"]),
                "updated_at": updated_at.isoformat(timespec="seconds"),
            }
        )
    return rows


def generate_equipment(payload: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    """Materialise the synthetic equipment ledger (Day-4 keeps this catalogue small)."""

    rows = []
    for entry in payload.get("equipment", []):
        last_service = as_of - timedelta(days=int(entry.get("days_since_maintenance", 30)))
        rows.append(
            {
                "equipment_code": str(entry["equipment_code"]),
                "area": str(entry["area"]),
                "equipment_type": str(entry["equipment_type"]),
                "status": str(entry["status"]),
                "last_maintenance_at": last_service.isoformat(),
            }
        )
    return rows


def generate_maintenance_records(payload: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    """Materialise maintenance dates from day offsets relative to ``as_of``."""

    rows = []
    for entry in payload.get("maintenance_records", []):
        service_date = as_of - timedelta(days=int(entry.get("maintenance_days_ago", 30)))
        rows.append(
            {
                "equipment_id": int(entry["equipment_id"]),
                "maintenance_type": str(entry["maintenance_type"]),
                "description": str(entry["description"]),
                "maintenance_date": service_date.isoformat(),
            }
        )
    return rows


def _catalog_rows(table: str, payload: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    """Catalogue rows keep the ids declared in the seed file (stable across re-seeds)."""

    rows = [dict(entry) for entry in payload.get(table, [])]
    if table == "users":
        created = datetime.combine(as_of, datetime.min.time()).isoformat(timespec="seconds")
        for row in rows:
            row.setdefault("created_at", created)
    return rows


#: ``(table key, ORM model, generator)`` in foreign-key-safe insert order.
TABLE_ORDER: tuple[
    tuple[str, type, Callable[[dict[str, Any], date], list[dict[str, Any]]] | None], ...
] = (
    ("users", User, None),
    ("suppliers", Supplier, None),
    ("materials", Material, None),
    ("purchase_orders", PurchaseOrder, generate_purchase_orders),
    ("inventory", Inventory, generate_inventory),
    ("safety_incidents", SafetyIncident, generate_safety_incidents),
    ("equipment", Equipment, generate_equipment),
    ("maintenance_records", MaintenanceRecord, generate_maintenance_records),
)

_MODEL_BY_TABLE = {key: model for key, model, _generator in TABLE_ORDER}


def seed_database(
    database: Database | None = None,
    *,
    payload: dict[str, Any] | None = None,
    as_of: date | None = None,
    force: bool = False,
) -> dict[str, int]:
    """Seed all demo tables and return ``{table: rows_inserted}`` (``{}`` if already seeded).

    Re-running without ``force`` is a no-op, so the demo can start any number of
    times without duplicating rows. ``force`` clears the tables first, which makes
    the whole dataset reproducible from ``seed.json``.
    """

    db = database or get_database()
    seed_payload = payload if payload is not None else load_seed()
    validate_seed(seed_payload)
    anchor = as_of or date.today()

    with db.session() as session:
        if not force and not _needs_seeding(session):
            logger.info("database already seeded, skipping", extra={"event": "db.seed.skip"})
            return {}
        if force:
            for _key, model, _generator in reversed(TABLE_ORDER):
                session.execute(delete(model))
            session.flush()

        counts: dict[str, int] = {}
        for key, model, generator in TABLE_ORDER:
            rows = (
                generator(seed_payload, anchor)
                if generator
                else _catalog_rows(key, seed_payload, anchor)
            )
            if not rows:
                continue
            session.bulk_insert_mappings(model, rows)
            counts[key] = len(rows)
        session.flush()

    logger.info(
        "synthetic database seeded",
        extra={"event": "db.seed", "db_path": db.path, "as_of": anchor.isoformat(), "rows": counts},
    )
    return counts


def _needs_seeding(session: Session) -> bool:
    return any(
        session.scalar(select(func.count()).select_from(_MODEL_BY_TABLE[table])) == 0
        for table in BUSINESS_TABLES
    )


def ensure_seeded(database: Database | None = None, *, as_of: date | None = None) -> dict[str, int]:
    """Idempotent bootstrap: create the schema, then seed it when still empty."""

    db = database or get_database()
    db.initialize()
    return seed_database(db, as_of=as_of)


def is_seeded(database: Database | None = None) -> bool:
    db = database or get_database()
    with db.session() as session:
        return not _needs_seeding(session)


def reset_business_data(database: Database | None = None) -> None:
    """Delete every business row (audit rows stay: they are the platform trail)."""

    db = database or get_database()
    with db.session() as session:
        for _key, model, _generator in reversed(TABLE_ORDER):
            session.execute(delete(model))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the synthetic Hengguang demo database.")
    parser.add_argument(
        "--force", action="store_true", help="clear the business tables and re-seed"
    )
    parser.add_argument("--as-of", dest="as_of", help="anchor date (YYYY-MM-DD) for generated rows")
    parser.add_argument(
        "--url", dest="url", help="database URL override (default: settings.database_url)"
    )
    args = parser.parse_args(argv)

    if args.url:
        update_settings(database_url=args.url)
    anchor = date.fromisoformat(args.as_of) if args.as_of else None
    counts = seed_database(get_database(), as_of=anchor, force=args.force)
    if counts:
        print(
            "seeded rows: "
            + ", ".join(f"{table}={count}" for table, count in sorted(counts.items()))
        )
    else:
        print("database already seeded (use --force to re-seed)")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
