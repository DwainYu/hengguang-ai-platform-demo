"""GET /metrics — operational counters as JSON (Day 4 §十二).

Kept public on purpose: a dashboard/poller should read it without impersonating a
user, and the payload only contains request/tool counters (no business data, no
identities). SPEC does not require Prometheus for Day 4, so this JSON document is
the whole observability surface; ``Metrics.snapshot`` is the single source.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import get_settings
from app.observability.metrics import metrics
from app.observability.middleware import endpoint_label, request_id_of

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def read_metrics(request: Request) -> dict:
    """Current metrics snapshot plus a little process context."""

    snapshot = metrics.snapshot()
    snapshot.update(
        {
            "app": {"version": get_settings().app_version, "provider": get_settings().llm_provider},
            "endpoint": endpoint_label(request.scope),
            "request_id": request_id_of(request),
        }
    )
    return snapshot
