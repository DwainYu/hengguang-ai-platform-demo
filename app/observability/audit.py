"""Audit trail (SPEC section 5.2 ``audit_logs``).

Two record shapes share one table:

* **API operations** — ``action`` like ``agent.run`` / ``knowledge.ingest`` with the
  endpoint, model, mode, status and latency of the request.
* **Tool calls** — one compact row per tool execution inside an agent loop
  (``action='tool.call'``, ``tool_name``, status, latency).

Privacy rules are enforced in one place (:meth:`AuditLog.record`): only compact
summaries are persisted, and a small denylist plus a key-size cap keep API keys,
Authorization headers, full prompts and document text out of the audit trail.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import text

from app.auth.auth import CurrentUser
from app.db.database import Database, get_database
from app.observability.metrics import Metrics
from app.observability.metrics import metrics as default_metrics

logger = logging.getLogger("app.observability.audit")

TABLE = "audit_logs"


#: Actions that must never be stored with the same tool/model columns.
class AuditAction:
    """Allowed ``action`` values (kept as a namespace so callers cannot typo them)."""

    CHAT_COMPLETE = "chat.complete"
    KNOWLEDGE_INGEST = "knowledge.ingest"
    KNOWLEDGE_SEARCH = "knowledge.search"
    KNOWLEDGE_DOCUMENTS = "knowledge.documents"
    AGENT_RUN = "agent.run"
    AUDIT_READ = "audit.read"
    MODELS_LIST = "models.list"
    TOOL_CALL = "tool.call"


class AuditStatus(StrEnum):
    """Terminal status of an audited action."""

    SUCCESS = "success"
    ERROR = "error"
    DENIED = "denied"
    UNAUTHENTICATED = "unauthenticated"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"


#: Never persisted, whatever a caller tries to pass in an input summary.
DENYLIST_TERMS = (
    "authorization",
    "api_key",
    "apikey",
    "x-api-key",
    "token",
    "secret",
    "password",
    "content",
    "text",
    "chunks",
    "prompt",
    "messages",
)

MAX_SUMMARY_VALUE_CHARS = 160
MAX_SUMMARY_KEYS = 12


@dataclass(frozen=True)
class Actor:
    """Who is executing right now: the authenticated demo user plus the request id.

    ``request_id`` is the single correlation key that ties HTTP → AgentRuntime →
    ToolExecutor → audit together, so one agent run produces one request id.
    """

    id: str = "anonymous"
    username: str = "anonymous"
    role: str = "anonymous"
    user_id: int | None = None
    request_id: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_user(cls, user: CurrentUser, request_id: str) -> Actor:
        return cls(
            id=user.id,
            username=user.username,
            role=user.role,
            user_id=user.user_id,
            request_id=request_id,
        )

    @classmethod
    def anonymous(cls, request_id: str = "") -> Actor:
        return cls(request_id=request_id)

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None


@dataclass(frozen=True)
class AuditEvent:
    """One audit record before it is written (or serialised for the tests)."""

    action: str
    status: str
    request_id: str = ""
    user_id: int | None = None
    username: str = ""
    role: str = ""
    endpoint: str | None = None
    tool_name: str | None = None
    model_name: str | None = None
    mode: str | None = None
    input_summary: dict[str, Any] = field(default_factory=dict)
    latency_ms: int | None = None
    created_at: str = ""

    @classmethod
    def build(
        cls,
        actor: Actor | None,
        *,
        action: str,
        status: str,
        endpoint: str | None = None,
        tool_name: str | None = None,
        model_name: str | None = None,
        mode: str | None = None,
        input_summary: dict[str, Any] | None = None,
        latency_ms: int | None = None,
    ) -> AuditEvent:
        who = actor or Actor.anonymous()
        return cls(
            action=action,
            status=status,
            request_id=who.request_id,
            user_id=who.user_id,
            username=who.username,
            role=who.role,
            endpoint=endpoint,
            tool_name=tool_name,
            model_name=model_name,
            mode=mode,
            input_summary=dict(input_summary or {}),
            latency_ms=latency_ms,
            created_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )

    def to_row(self) -> dict[str, Any]:
        """Database row (SPEC columns); ``username``/``role`` stay display-only."""

        return {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "action": self.action,
            "endpoint": self.endpoint,
            "tool_name": self.tool_name,
            "model_name": self.model_name,
            "mode": self.mode,
            "input_summary": json.dumps(
                sanitize_summary(self.input_summary), ensure_ascii=False, default=str
            ),
            "status": self.status,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        """Public API shape returned by ``GET /api/audit``."""

        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "action": self.action,
            "endpoint": self.endpoint,
            "operation": self.action,
            "tool": self.tool_name,
            "model": self.model_name,
            "mode": self.mode,
            "input_summary": sanitize_summary(self.input_summary),
            "status": self.status,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }


def sanitize_summary(summary: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only small, non-sensitive fields from a proposed input summary."""

    if not summary:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in summary.items():
        name = str(key)
        lowered = name.lower()
        if len(cleaned) >= MAX_SUMMARY_KEYS:
            break
        if any(term in lowered for term in DENYLIST_TERMS):
            continue
        if isinstance(value, (dict, list, tuple, set)):
            cleaned[name] = len(value)
        elif isinstance(value, (int, float, bool)) or value is None:
            cleaned[name] = value
        else:
            cleaned[name] = str(value)[:MAX_SUMMARY_VALUE_CHARS]
    return cleaned


_INSERT_SQL = """
INSERT INTO audit_logs (
    user_id, request_id, action, endpoint, tool_name, model_name, mode,
    input_summary, status, latency_ms, created_at
) VALUES (
    :user_id, :request_id, :action, :endpoint, :tool_name, :model_name, :mode,
    :input_summary, :status, :latency_ms, :created_at
)
"""

_SELECT_SQL = """
SELECT
    a.id, a.request_id, a.user_id, a.action, a.endpoint, a.tool_name, a.model_name,
    a.mode, a.input_summary, a.status, a.latency_ms, a.created_at,
    u.username AS username, u.role AS role
FROM audit_logs a
LEFT JOIN users u ON u.id = a.user_id
{where}
ORDER BY a.id DESC
LIMIT :limit OFFSET :offset
"""

_COUNT_SQL = "SELECT COUNT(*) FROM audit_logs a {where}"

#: Supported ``GET /api/audit`` filters: filter name → SQL fragment.
_FILTERS = {
    "tool": "a.tool_name = :tool",
    "action": "a.action = :action",
    "status": "a.status = :status",
    "request_id": "a.request_id = :request_id",
    "user_id": "a.user_id = :user_id",
}


class AuditLog:
    """Writes and reads audit rows; writing never breaks the request it records."""

    def __init__(
        self,
        database: Callable[[], Database] = get_database,
        *,
        metrics: Metrics | None = None,
    ) -> None:
        self._database = database
        self._metrics = metrics if metrics is not None else default_metrics
        self._records: list[AuditEvent] = []
        self._last_error: Exception | None = None

    @property
    def records(self) -> tuple[AuditEvent, ...]:
        """Events prepared by this instance (inspection + test hook)."""

        return tuple(self._records)

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def record(self, event: AuditEvent) -> AuditEvent:
        """Persist one event (best effort) and always keep it in memory.

        ``audit_logs.user_id`` is NOT NULL in SPEC section 5.2, so events without an
        authenticated user (401 attempts) are kept in memory and in the structured
        log only — they can never break the table's contract.
        """

        self._records.append(event)
        if event.user_id is None:
            logger.debug(
                "audit event without a known user is not persisted",
                extra={"event": "audit.skip", "action": event.action, "status": event.status},
            )
            return event
        try:
            db = self._database()
            if not db.is_initialized:
                return event
            with db.session() as session:
                session.execute(text(_INSERT_SQL), event.to_row())
            self._metrics.observe_audit_write()
        except Exception as exc:  # audit must never take down the API
            self._last_error = exc
            logger.warning(
                "audit write failed",
                extra={
                    "event": "audit.write_error",
                    "action": event.action,
                    "error_type": type(exc).__name__,
                },
            )
        return event

    def record_api(
        self,
        actor: Actor | CurrentUser | None,
        *,
        action: str,
        status: str,
        endpoint: str | None = None,
        request_id: str = "",
        model_name: str | None = None,
        mode: str | None = None,
        input_summary: dict[str, Any] | None = None,
        latency_ms: int | None = None,
    ) -> AuditEvent:
        """Record an API-level operation from either an :class:`Actor` or a user."""

        return self.record(
            AuditEvent.build(
                _coerce_actor(actor, request_id),
                action=action,
                status=status,
                endpoint=endpoint,
                model_name=model_name,
                mode=mode,
                input_summary=input_summary,
                latency_ms=latency_ms,
            )
        )

    def record_tool_call(
        self,
        actor: Actor | CurrentUser | None,
        *,
        tool_name: str,
        status: str,
        request_id: str = "",
        model_name: str | None = None,
        mode: str = "agent",
        input_summary: dict[str, Any] | None = None,
        latency_ms: int | None = None,
    ) -> AuditEvent:
        """Compact one-row-per-tool-call record for agent tool executions."""

        return self.record(
            AuditEvent.build(
                _coerce_actor(actor, request_id),
                action=AuditAction.TOOL_CALL,
                status=status,
                endpoint="agent.tool",
                tool_name=tool_name,
                model_name=model_name,
                mode=mode,
                input_summary=input_summary,
                latency_ms=latency_ms,
            )
        )

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        tool: str | None = None,
        action: str | None = None,
        status: str | None = None,
        request_id: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """Paginated audit view: ``{items, page, page_size, total}`` (newest first)."""

        page = max(1, int(page))
        page_size = max(1, min(100, int(page_size)))
        candidate_filters = {
            "tool": tool,
            "action": action,
            "status": status,
            "request_id": request_id,
            "user_id": user_id,
        }
        selected = {
            name: value for name, value in candidate_filters.items() if value not in (None, "")
        }
        clauses = [_FILTERS[name] for name in selected]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params = dict(selected)
        params.update({"limit": page_size, "offset": (page - 1) * page_size})

        db = self._database()
        if not db.is_initialized:
            return {"items": [], "page": page, "page_size": page_size, "total": 0}
        with db.session() as session:
            total = int(session.execute(text(_COUNT_SQL.format(where=where)), params).scalar_one())
            rows = session.execute(text(_SELECT_SQL.format(where=where)), params).mappings().all()
        return {
            "items": [_row_to_item(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def count(self) -> int:
        db = self._database()
        if not db.is_initialized:
            return len(self._records)
        return db.table_row_count(TABLE)

    def clear(self) -> None:
        """Drop in-memory events (used by tests). DB rows are kept on purpose."""

        self._records = []
        self._last_error = None


def _coerce_actor(actor: Actor | CurrentUser | None, request_id: str) -> Actor | None:
    if actor is None:
        return None
    if isinstance(actor, Actor):
        return actor
    if isinstance(actor, CurrentUser):
        return Actor.from_user(actor, request_id)
    raise TypeError(f"unsupported audit actor: {type(actor).__name__}")


def _row_to_item(row: Any) -> dict[str, Any]:
    summary = row["input_summary"]
    try:
        parsed = json.loads(summary) if summary else {}
    except (TypeError, ValueError):
        parsed = {"detail": str(summary)[:MAX_SUMMARY_VALUE_CHARS]}
    return {
        "id": row["id"],
        "request_id": row["request_id"],
        "user_id": row["user_id"],
        "username": row["username"] or "",
        "role": row["role"] or "",
        "action": row["action"],
        "endpoint": row["endpoint"],
        "operation": row["action"],
        "tool": row["tool_name"],
        "model": row["model_name"],
        "mode": row["mode"],
        "input_summary": parsed,
        "status": row["status"],
        "latency_ms": row["latency_ms"],
        "created_at": row["created_at"],
    }


_audit_log: AuditLog | None = None


def get_audit_log() -> AuditLog:
    """Process-wide audit log (resolves the database singleton per write)."""

    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


def set_audit_log(audit_log: AuditLog | None) -> None:
    """Replace the process-wide audit log (tests / custom wiring)."""

    global _audit_log
    _audit_log = audit_log


__all__ = [
    "AuditStatus",
    "AuditAction",
    "AuditEvent",
    "AuditLog",
    "DENYLIST_TERMS",
    "Actor",
    "get_audit_log",
    "sanitize_summary",
    "set_audit_log",
]
