"""Per-request middleware: request_id correlation, access log and metrics.

One pure-ASGI middleware does three small jobs (Day 4 §十一):

1. resolve or generate ``req_<uuid4>`` and bind it to the logging context,
2. time the request and feed :class:`app.observability.metrics.Metrics`,
3. emit one structured log line per request.

The id is echoed back in the ``X-Request-ID`` response header, stored in
``scope["state"]["request_id"]`` (so dependencies can read it) and exposed through
:func:`app.observability.logging.current_request_id`. That single value is what
travels HTTP → AgentRuntime → ToolExecutor → AuditLog for one run.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import MutableMapping
from typing import Any

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.observability.logging import REQUEST_ID_HEADER, current_request_id, request_id_scope
from app.observability.metrics import metrics

logger = logging.getLogger("app.observability.http")

State = MutableMapping[str, Any]


def new_request_id() -> str:
    """Generate a request id (honours a caller-supplied ``X-Request-ID``)."""

    return f"req_{uuid.uuid4()}"


class RequestContextMiddleware:
    """Pure ASGI middleware: no response buffering, safe for future streaming."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state: State = scope.setdefault("state", {})
        request_id = _incoming_request_id(scope) or state.get("request_id") or new_request_id()
        state["request_id"] = request_id
        started = time.perf_counter()
        outcome: dict[str, Any] = {"status_code": 0}
        original_send = send

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                outcome["status_code"] = int(message["status"])
                headers: list[tuple[bytes, bytes]] = message.setdefault("headers", [])
                if not any(
                    name.decode("latin-1").lower() == REQUEST_ID_HEADER.lower()
                    for name, _ in headers
                ):
                    headers.append(
                        (REQUEST_ID_HEADER.encode("latin-1"), request_id.encode("latin-1"))
                    )
            await original_send(message)

        try:
            with request_id_scope(request_id):
                await self.app(scope, receive, send_wrapper)
        except Exception:
            self._observe(scope, state, outcome, started, request_id, fallback_status=500)
            logger.exception(
                "request failed",
                extra={
                    "event": "http.request",
                    "endpoint": endpoint_label(scope),
                    "request_id": request_id,
                },
            )
            raise
        self._observe(scope, state, outcome, started, request_id, fallback_status=200)

    def _observe(
        self,
        scope: Scope,
        state: State,
        outcome: dict[str, Any],
        started: float,
        request_id: str,
        *,
        fallback_status: int,
    ) -> None:
        latency_ms = (time.perf_counter() - started) * 1000
        status_code = int(outcome.get("status_code") or fallback_status)
        error_code = state.get("error_code")
        endpoint = endpoint_label(scope)
        metrics.observe_request(
            endpoint=endpoint,
            status_code=status_code,
            latency_ms=latency_ms,
            error_code=error_code,
        )
        level = logging.WARNING if status_code >= 500 else logging.INFO
        logger.log(
            level,
            "request failed" if error_code and status_code >= 500 else "request completed",
            extra={
                "event": "http.request",
                "endpoint": endpoint,
                "method": scope.get("method", ""),
                "status": status_code,
                "latency_ms": round(latency_ms, 2),
                "error_code": error_code,
                "request_id": request_id,
            },
        )


def _incoming_request_id(scope: Scope) -> str | None:
    for name, value in scope.get("headers", []) or []:
        if name.decode("latin-1").lower() == REQUEST_ID_HEADER.lower():
            raw = value.decode("latin-1").strip()
            if raw and len(raw) <= 128:
                return raw
    return current_request_id() or None


def request_id_of(request: Request) -> str:
    """FastAPI dependency: the request id bound by the middleware."""

    state = getattr(request, "state", None)
    value = getattr(state, "request_id", "") if state is not None else ""
    return value or current_request_id() or new_request_id()


def endpoint_label(scope: Scope) -> str:
    """``"POST /api/agent/run"`` — route template when matched, path otherwise."""

    method = scope.get("method", "GET")
    route = scope.get("route")
    path = getattr(route, "path", None) or scope.get("path", "")
    return f"{method} {path}"


__all__ = ["RequestContextMiddleware", "endpoint_label", "new_request_id", "request_id_of"]
