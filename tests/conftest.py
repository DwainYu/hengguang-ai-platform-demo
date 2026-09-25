"""Shared test fixtures for the whole suite.

Two things Day 4 needs that individual test files must not repeat:

1. **A seeded, throw-away SQLite database.** The process-wide database singleton is
   pointed at a session temporary file and seeded from ``data/synthetic`` with a
   fixed anchor date, so business tools, the audit trail and the API all read the
   same deterministic synthetic data — and the repository's ``data/runtime`` stays
   untouched by tests.

2. **An identity for the Day-1..3 integration tests.** Those tests predate RBAC and
   call the API without an ``Authorization`` header. Production behaviour is *not*
   weakened for their sake: only the ``get_current_user`` dependency is overridden
   with the demo admin, exactly the FastAPI-documented way to test protected routes.
   Files marked ``@pytest.mark.real_auth`` (or the RBAC tests themselves) drop the
   override and exercise the real 401 / 403 path.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.auth import DEMO_ADMIN
from app.auth.dependencies import get_current_user
from app.config import update_settings
from app.db.database import Database, set_database
from app.db.seed import ensure_seeded, load_seed, validate_seed
from app.main import app
from app.observability.audit import AuditLog, get_audit_log, set_audit_log
from app.observability.metrics import metrics

REAL_AUTH_MARKER = "real_auth"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", f"{REAL_AUTH_MARKER}: do not auto-authenticate as the demo admin"
    )


@pytest.fixture(scope="session")
def seeded_database(tmp_path_factory) -> Database:
    """Session-wide temporary SQLite database seeded with the synthetic demo data.

    Deterministic (fixed ``meta.random_seed``) and isolated from the repository's
    ``data/runtime`` directory.
    """

    path = tmp_path_factory.mktemp("hengguang-db") / "demo.db"
    database = Database(url=f"sqlite:///{path}")
    update_settings(database_url=database.url)
    set_database(database)
    database.initialize()
    # Seeded relative to today so that "the last 30 days" always contains rows,
    # exactly like the demo database the platform creates on first start.
    ensure_seeded(database)
    metrics.reset()
    set_audit_log(AuditLog())
    yield database
    set_audit_log(None)
    database.dispose()
    set_database(None)
    update_settings(database_url="sqlite:///./data/runtime/app.db")


@pytest.fixture
def audit_log(seeded_database: Database) -> AuditLog:
    """The process-wide audit recorder (installed by ``seeded_database``)."""

    return get_audit_log()


@pytest.fixture(autouse=True)
def demo_platform_database(seeded_database: Database) -> None:
    """Make every test (including the Day-1..3 ones) use the seeded demo database."""

    assert seeded_database.is_initialized
    yield


@pytest.fixture(autouse=True)
def legacy_demo_identity(request, seeded_database: Database) -> None:
    """Install the demo admin identity for unauthenticated legacy tests.

    Skipped for modules/functions marked ``real_auth``, which test the token path
    itself.
    """

    if request.node.get_closest_marker(REAL_AUTH_MARKER):
        yield
        return
    app.dependency_overrides[get_current_user] = lambda: DEMO_ADMIN
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client(seeded_database: Database) -> TestClient:
    """TestClient with the legacy demo-admin identity (Day-1..3 style requests)."""

    return TestClient(app)


@pytest.fixture
def platform_client(seeded_database: Database) -> TestClient:
    """TestClient that runs the lifespan (schema + seed) and uses the real app."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def synthetic_seed() -> dict:
    """The synthetic seed file, validated (used by the data-layer tests)."""

    payload = load_seed()
    validate_seed(payload)
    return payload
