"""SQLite access for the synthetic business tables and the platform audit log.

The engine is created lazily so importing the application never touches the disk,
and relative SQLite paths are resolved against the repository root (never the
current working directory). Tests install their own database with
:func:`set_database` before serving requests.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session

from app.config import BASE_DIR, get_settings
from app.db.models import Base

logger = logging.getLogger("app.db")


def resolve_sqlite_path(raw_path: str) -> Path:
    """Make a relative SQLite path repository-relative, so the CWD does not matter."""

    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def normalize_url(url: str) -> str:
    """Return ``url`` with any relative SQLite file path made absolute."""

    if not url.startswith("sqlite"):
        return url
    raw = url.split("///", 1)[-1]
    if not raw or raw == ":memory:" or "/" not in raw:
        return url
    return f"sqlite:///{resolve_sqlite_path(raw)}"


class Database:
    """Thin wrapper around a SQLAlchemy engine with explicit, bounded sessions."""

    def __init__(self, url: str | None = None, *, echo: bool = False) -> None:
        self.url = normalize_url(url or get_settings().database_url)
        self.echo = echo
        self._engine: Engine | None = None
        self._lock = threading.Lock()
        self._initialized = False

    @property
    def is_sqlite(self) -> bool:
        return self.url.startswith("sqlite")

    @property
    def path(self) -> str:
        """Filesystem path of the SQLite file (empty string for non-sqlite URLs)."""

        if not self.is_sqlite:
            return ""
        return self.url.split("///", 1)[-1] or ":memory:"

    @property
    def engine(self) -> Engine:
        with self._lock:
            if self._engine is None:
                if self.is_sqlite and self.path not in {"", ":memory:"}:
                    Path(self.path).parent.mkdir(parents=True, exist_ok=True)
                self._engine = create_engine(self.url, echo=self.echo, future=True)
                if self.is_sqlite:
                    event.listens_for(self._engine, "connect")(_enable_foreign_keys)
            return self._engine

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, *, force: bool = False) -> bool:
        """Create the SPEC tables when missing. Returns ``True`` on first creation."""

        if self._initialized and not force:
            return False
        Base.metadata.create_all(self.engine)
        self._initialized = True
        logger.info("database ready", extra={"event": "db.init", "db_path": self.path})
        return True

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Context-managed session: commits on success, rolls back on failure."""

        self.initialize()
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def query(self, sql: str, params: dict | None = None) -> list[dict]:
        """Run a fixed parameterized ``SELECT`` and return the rows as dicts."""

        with self.session() as session:
            result = session.execute(text(sql), params or {})
            return [dict(row) for row in result.mappings().all()]

    def scalar(self, sql: str, params: dict | None = None):
        """Run a fixed parameterized query and return the first column of row one."""

        with self.session() as session:
            return session.execute(text(sql), params or {}).scalar()

    def table_row_count(self, table_name: str) -> int:
        """Row count of one SPEC table (used by the seeding check and by tests)."""

        if table_name not in Base.metadata.tables:
            raise KeyError(f"unknown table '{table_name}'")
        quoted = table_name.replace('"', '""')
        return int(self.scalar(f'SELECT COUNT(*) FROM "{quoted}"'))

    def is_empty(self, table_names: tuple[str, ...]) -> bool:
        """True when every listed table still has zero rows."""

        return all(self.table_row_count(name) == 0 for name in table_names)

    def dispose(self) -> None:
        """Drop the engine (used when a test swaps the database out)."""

        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._initialized = False

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Database(url={self.url!r}, initialized={self._initialized})"


def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_database: Database | None = None
_database_lock = threading.Lock()


def get_database() -> Database:
    """Process-wide database instance built from the current ``DATABASE_URL``."""

    global _database
    with _database_lock:
        wanted = normalize_url(get_settings().database_url)
        if _database is None or _database.url != wanted:
            _database = Database(wanted)
        return _database


def set_database(database: Database | None) -> None:
    """Install a database instance (used by the demo bootstrap and by tests)."""

    global _database
    with _database_lock:
        if _database is not None and _database is not database:
            _database.dispose()
        _database = database


__all__ = ["BASE_DIR", "Database", "get_database", "normalize_url", "set_database"]
