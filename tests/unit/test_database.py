"""Unit tests for the Day-4 data layer: schema parity, deterministic seeding, safety.

The synthetic database is the only "enterprise data" the demo touches, so these
tests pin down three promises:

1. the ORM matches ``data/synthetic/schema.sql`` (SPEC section 5) table-for-table,
2. seeding is deterministic and repeatable (same anchor date → same rows),
3. business tables are populated and reachable through fixed parameterized queries.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import BASE_DIR
from app.db.database import Database, normalize_url
from app.db.models import Base
from app.db.seed import (
    BUSINESS_TABLES,
    SeedValidationError,
    ensure_seeded,
    generate_purchase_orders,
    generate_safety_incidents,
    is_seeded,
    load_seed,
    seed_database,
    validate_seed,
)

SCHEMA_PATH = BASE_DIR / "data" / "synthetic" / "schema.sql"
CREATE_TABLE_RE = re.compile(r"CREATE TABLE (\w+) \((.*?)\n\);", re.DOTALL)
_CONSTRAINT_WORDS = ("primary", "foreign", "unique", "check", "constraint")


def _schema_sql_tables() -> dict[str, set[str]]:
    """``{table: {column}}`` parsed from the hand-written reference schema."""

    ddl = SCHEMA_PATH.read_text(encoding="utf-8")
    tables: dict[str, set[str]] = {}
    for name, body in CREATE_TABLE_RE.findall(ddl):
        columns = set()
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            if not line or line.startswith("--"):
                continue
            first = line.split()[0].lower()
            if first in _CONSTRAINT_WORDS:
                continue
            columns.add(line.split()[0])
        tables[name] = columns
    return tables


@pytest.fixture
def fresh_database(tmp_path) -> Database:
    database = Database(url=f"sqlite:///{tmp_path / 'business.db'}")
    database.initialize()
    return database


class TestSchemaConsistency:
    def test_reference_schema_covers_the_spec_tables(self):
        tables = _schema_sql_tables()
        assert set(tables) == {
            "users",
            "audit_logs",
            "suppliers",
            "materials",
            "purchase_orders",
            "inventory",
            "safety_incidents",
            "equipment",
            "maintenance_records",
        }

    def test_orm_and_reference_schema_describe_the_same_tables(self):
        sql_tables = _schema_sql_tables()
        orm_tables = set(Base.metadata.tables)
        assert orm_tables == set(sql_tables)

    @pytest.mark.parametrize("table", sorted(set(Base.metadata.tables)))
    def test_orm_and_reference_schema_describe_the_same_columns(self, table):
        assert _schema_sql_tables()[table] == set(Base.metadata.tables[table].columns.keys()), table

    def test_audit_logs_records_the_platform_fields(self):
        columns = set(Base.metadata.tables["audit_logs"].columns.keys())
        assert {
            "user_id",
            "request_id",
            "action",
            "endpoint",
            "tool_name",
            "model_name",
            "mode",
            "input_summary",
            "status",
            "latency_ms",
            "created_at",
        } <= columns


class TestSeedValidation:
    def test_shipped_seed_is_valid(self, synthetic_seed):
        assert validate_seed(synthetic_seed) is None
        assert synthetic_seed["meta"]["disclaimer"]

    def test_every_row_is_declared_synthetic(self):
        payload = json.loads(
            (BASE_DIR / "data" / "synthetic" / "seed.json").read_text(encoding="utf-8")
        )
        assert "合成" in payload["meta"]["disclaimer"]

    def test_unknown_material_reference_is_rejected(self, synthetic_seed):
        synthetic_seed["inventory"].append(
            {"material_id": 999, "warehouse": "x", "quantity": 1, "updated_days_ago": 0}
        )
        with pytest.raises(SeedValidationError, match="unknown material"):
            validate_seed(synthetic_seed)

    def test_unknown_supplier_material_link_is_rejected(self, synthetic_seed):
        synthetic_seed["supplier_preferred_material_ids"]["1"] = [42]
        with pytest.raises(SeedValidationError, match="unknown material"):
            validate_seed(synthetic_seed)

    @pytest.mark.parametrize("group", ["areas", "categories", "severities", "statuses"])
    def test_zero_weight_is_rejected(self, synthetic_seed, group):
        synthetic_seed["safety"][group][0]["weight"] = 0
        with pytest.raises(SeedValidationError, match="positive weights"):
            validate_seed(synthetic_seed)

    def test_missing_descriptions_are_rejected(self, synthetic_seed):
        synthetic_seed["safety"]["descriptions"].pop("设备泄漏与隐患")
        with pytest.raises(SeedValidationError, match="missing"):
            validate_seed(synthetic_seed)


class TestSeeding:
    def test_seed_populates_every_business_table(self, fresh_database):
        counts = seed_database(fresh_database, as_of=date(2026, 9, 26))
        assert counts["users"] == 3
        for table in BUSINESS_TABLES:
            assert counts[table] > 0, table
            assert fresh_database.table_row_count(table) == counts[table]

    def test_seeding_is_deterministic_for_a_fixed_anchor_date(self, tmp_path):
        first = Database(url=f"sqlite:///{tmp_path / 'a.db'}")
        second = Database(url=f"sqlite:///{tmp_path / 'b.db'}")
        anchor = date(2026, 6, 15)
        seed_database(first, as_of=anchor)
        seed_database(second, as_of=anchor)
        assert first.query("SELECT * FROM purchase_orders ORDER BY id") == second.query(
            "SELECT * FROM purchase_orders ORDER BY id"
        )
        assert first.query("SELECT * FROM safety_incidents ORDER BY id") == second.query(
            "SELECT * FROM safety_incidents ORDER BY id"
        )

    def test_generator_output_is_stable(self, synthetic_seed):
        anchor = date(2026, 9, 26)
        rows = generate_purchase_orders(synthetic_seed, anchor)
        again = generate_purchase_orders(synthetic_seed, anchor)
        assert rows == again
        incidents = generate_safety_incidents(synthetic_seed, anchor)
        assert incidents == generate_safety_incidents(synthetic_seed, anchor)

    def test_re_running_seed_does_not_duplicate_rows(self, fresh_database):
        first = seed_database(fresh_database, as_of=date(2026, 9, 26))
        assert first
        assert seed_database(fresh_database, as_of=date(2026, 9, 26)) == {}
        assert fresh_database.table_row_count("purchase_orders") == first["purchase_orders"]
        assert is_seeded(fresh_database) is True

    def test_force_reseed_rebuilds_the_same_data(self, fresh_database):
        anchor = date(2026, 9, 26)
        seed_database(fresh_database, as_of=anchor)
        before = fresh_database.query("SELECT * FROM purchase_orders ORDER BY id")
        counts = seed_database(fresh_database, as_of=anchor, force=True)
        assert counts["purchase_orders"] == len(before)
        after = fresh_database.query("SELECT * FROM purchase_orders ORDER BY id")
        assert after == before

    def test_history_covers_the_request_window(self, fresh_database):
        anchor = date(2026, 9, 26)
        seed_database(fresh_database, as_of=anchor)
        rows = fresh_database.query(
            "SELECT MIN(order_date) AS first, MAX(order_date) AS last FROM purchase_orders"
        )
        assert rows[0]["last"] == anchor.isoformat()
        assert rows[0]["first"] <= (anchor - timedelta(days=110)).isoformat()
        recent = fresh_database.query(
            "SELECT COUNT(*) AS c FROM purchase_orders WHERE order_date >= :cutoff",
            {"cutoff": (anchor - timedelta(days=29)).isoformat()},
        )
        assert recent[0]["c"] > 20

    def test_safety_incidents_span_areas_and_severities(self, fresh_database):
        seed_database(fresh_database, as_of=date(2026, 9, 26))
        areas = fresh_database.query("SELECT DISTINCT area FROM safety_incidents")
        severities = fresh_database.query("SELECT DISTINCT severity FROM safety_incidents")
        assert len(areas) >= 5
        assert {row["severity"] for row in severities} == {"low", "medium", "high", "critical"}

    def test_demo_users_are_seeded_with_their_roles(self, fresh_database):
        seed_database(fresh_database, as_of=date(2026, 9, 26))
        rows = fresh_database.query("SELECT id, username, role FROM users ORDER BY id")
        assert [(row["id"], row["role"]) for row in rows] == [
            (1, "admin"),
            (2, "manager"),
            (3, "operator"),
        ]

    def test_ensure_seeded_creates_schema_and_data(self, tmp_path):
        database = Database(url=f"sqlite:///{tmp_path / 'lazy.db'}")
        assert database.is_initialized is False
        counts = ensure_seeded(database, as_of=date(2026, 9, 26))
        assert counts and database.is_initialized
        assert ensure_seeded(database, as_of=date(2026, 9, 26)) == {}

    def test_seed_cli_reports_the_row_counts(self, tmp_path, capsys):
        from app.db.seed import main as seed_main

        url = f"sqlite:///{tmp_path / 'cli.db'}"
        assert seed_main(["--url", url, "--as-of", "2026-09-26"]) == 0
        printed = capsys.readouterr().out
        assert "purchase_orders=" in printed
        assert seed_main(["--url", url, "--as-of", "2026-09-26"]) == 0
        assert "already seeded" in capsys.readouterr().out


class TestDatabaseBehaviour:
    def test_relative_sqlite_paths_resolve_against_the_repository(self):
        assert normalize_url("sqlite:///./data/runtime/app.db").startswith(f"sqlite:///{BASE_DIR}")

    def test_sessions_create_the_schema_on_demand(self, tmp_path):
        database = Database(url=f"sqlite:///{tmp_path / 'auto.db'}")
        assert database.table_row_count("suppliers") == 0
        assert database.is_initialized

    def test_unknown_table_count_is_rejected(self, fresh_database):
        with pytest.raises(KeyError, match="unknown table"):
            fresh_database.table_row_count("not_a_table")

    def test_foreign_keys_are_enforced(self, fresh_database):
        """SQLite FK enforcement is on, so bogus business rows cannot be inserted."""

        statement = text(
            "INSERT INTO purchase_orders "
            "(supplier_id, material_id, quantity, unit_price, order_date, status) "
            "VALUES (999, 999, 1, 1, '2026-09-01', 'draft')"
        )
        with pytest.raises(IntegrityError), fresh_database.session() as session:
            session.execute(statement)
        assert fresh_database.table_row_count("purchase_orders") == 0

    def test_seed_file_path_is_configurable(self):
        assert load_seed(Path("data/synthetic/seed.json"))["users"]
