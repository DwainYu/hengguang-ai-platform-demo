"""In-process request/tool counters exposed as JSON at ``GET /metrics`` (Day 4).

No Prometheus / Grafana is required by SPEC for Day 4, so the counters live here:
a handful of monotone totals plus latency averages, resettable for tests. The
Day-5 dashboard can read the same JSON, and a Prometheus exporter would only be a
thin serialiser on top of :meth:`Metrics.snapshot`.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class Metrics:
    """Thread-safe counters for requests, tools, agent runs and errors."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.monotonic()
        self._requests = 0
        self._successes = 0
        self._errors = 0
        self._latency_total_ms = 0.0
        self._latency_count = 0
        self._max_latency_ms = 0.0
        self._by_endpoint: dict[str, dict[str, float]] = {}
        self._by_status: dict[str, int] = {}
        self._error_codes: dict[str, int] = {}
        self._tool_calls = 0
        self._tool_failures = 0
        self._permission_denied = 0
        self._agent_runs = 0
        self._agent_run_status: dict[str, int] = {}
        self._audit_writes = 0

    def reset(self) -> None:
        with self._lock:
            self.__init__()

    def observe_request(
        self,
        *,
        endpoint: str,
        status_code: int,
        latency_ms: float,
        error_code: str | None = None,
    ) -> None:
        """Record one finished HTTP request."""

        with self._lock:
            self._requests += 1
            self._latency_total_ms += latency_ms
            self._latency_count += 1
            self._max_latency_ms = max(self._max_latency_ms, latency_ms)
            bucket = self._by_endpoint.setdefault(endpoint, {"count": 0, "latency_ms": 0.0})
            bucket["count"] += 1
            bucket["latency_ms"] += latency_ms
            key = f"{status_code // 100}xx"
            self._by_status[key] = self._by_status.get(key, 0) + 1
            if status_code < 400:
                self._successes += 1
            else:
                self._errors += 1
                if error_code:
                    self._error_codes[error_code] = self._error_codes.get(error_code, 0) + 1

    def observe_tool_call(
        self, *, tool: str, success: bool, permission_denied: bool = False
    ) -> None:
        """Record one tool execution (including failures and denied calls)."""

        with self._lock:
            self._tool_calls += 1
            if not success:
                self._tool_failures += 1
            if permission_denied:
                self._permission_denied += 1

    def observe_agent_run(self, *, status: str) -> None:
        """Record one completed agent run (``status`` is the runtime status string)."""

        with self._lock:
            self._agent_runs += 1
            self._agent_run_status[status] = self._agent_run_status.get(status, 0) + 1

    def observe_audit_write(self) -> None:
        with self._lock:
            self._audit_writes += 1

    @property
    def request_count(self) -> int:
        return self._requests

    @property
    def tool_call_count(self) -> int:
        return self._tool_calls

    def snapshot(self) -> dict[str, Any]:
        """JSON-serialisable metrics document served by ``GET /metrics``."""

        with self._lock:
            average = self._latency_total_ms / self._latency_count if self._latency_count else 0.0
            endpoints = {
                name: {
                    "count": int(values["count"]),
                    "avg_latency_ms": (
                        round(values["latency_ms"] / values["count"], 2) if values["count"] else 0.0
                    ),
                }
                for name, values in sorted(self._by_endpoint.items())
            }
            return {
                "request_count": self._requests,
                "success_count": self._successes,
                "error_count": self._errors,
                "avg_latency_ms": round(average, 2),
                "max_latency_ms": round(self._max_latency_ms, 2),
                "requests_by_status_class": dict(sorted(self._by_status.items())),
                "requests_by_endpoint": endpoints,
                "error_by_code": dict(sorted(self._error_codes.items())),
                "tool_call_count": self._tool_calls,
                "tool_error_count": self._tool_failures,
                "permission_denied_count": self._permission_denied,
                "agent_run_count": self._agent_runs,
                "agent_runs_by_status": dict(sorted(self._agent_run_status.items())),
                "audit_write_count": self._audit_writes,
                "uptime_seconds": round(time.monotonic() - self._started_at, 2),
            }


#: Process-wide metrics instance used by the middleware, executor and audit layer.
metrics = Metrics()

__all__ = ["Metrics", "metrics"]
