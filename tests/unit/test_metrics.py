"""Unit tests for the in-process metrics counters behind ``GET /metrics``."""

from __future__ import annotations

from app.observability.metrics import Metrics

REQUIRED_KEYS = {
    "request_count",
    "success_count",
    "error_count",
    "avg_latency_ms",
    "tool_call_count",
}


class TestSnapshotShape:
    def test_snapshot_contains_the_day4_keys(self):
        snapshot = Metrics().snapshot()
        assert REQUIRED_KEYS <= set(snapshot)

    def test_fresh_counter_starts_empty(self):
        snapshot = Metrics().snapshot()
        assert snapshot["request_count"] == 0
        assert snapshot["avg_latency_ms"] == 0.0
        assert snapshot["tool_call_count"] == 0


class TestRequestCounters:
    def test_success_and_error_split(self):
        metrics = Metrics()
        metrics.observe_request(endpoint="GET /health", status_code=200, latency_ms=10)
        metrics.observe_request(endpoint="POST /api/chat", status_code=302, latency_ms=20)
        metrics.observe_request(
            endpoint="GET /api/audit", status_code=403, latency_ms=5, error_code="PERMISSION_DENIED"
        )
        metrics.observe_request(
            endpoint="GET /api/nope", status_code=404, latency_ms=1, error_code="NOT_FOUND"
        )
        metrics.observe_request(
            endpoint="POST /api/chat", status_code=500, latency_ms=50, error_code="INTERNAL_ERROR"
        )
        snapshot = metrics.snapshot()
        assert snapshot["request_count"] == 5
        assert snapshot["success_count"] == 2
        assert snapshot["error_count"] == 3
        assert snapshot["avg_latency_ms"] == 17.2
        assert snapshot["max_latency_ms"] == 50.0

    def test_error_codes_are_tallied(self):
        metrics = Metrics()
        for _ in range(3):
            metrics.observe_request(
                endpoint="GET /api/audit",
                status_code=401,
                latency_ms=2,
                error_code="UNAUTHENTICATED",
            )
        assert metrics.snapshot()["error_by_code"] == {"UNAUTHENTICATED": 3}

    def test_per_endpoint_counters(self):
        metrics = Metrics()
        metrics.observe_request(endpoint="POST /api/agent/run", status_code=200, latency_ms=100)
        metrics.observe_request(endpoint="POST /api/agent/run", status_code=200, latency_ms=200)
        by_endpoint = metrics.snapshot()["requests_by_endpoint"]
        assert by_endpoint["POST /api/agent/run"]["count"] == 2
        assert by_endpoint["POST /api/agent/run"]["avg_latency_ms"] == 150.0

    def test_status_class_histogram(self):
        metrics = Metrics()
        metrics.observe_request(endpoint="GET /health", status_code=200, latency_ms=1)
        metrics.observe_request(endpoint="GET /health", status_code=404, latency_ms=1)
        metrics.observe_request(endpoint="GET /health", status_code=503, latency_ms=1)
        assert metrics.snapshot()["requests_by_status_class"] == {"2xx": 1, "4xx": 1, "5xx": 1}


class TestToolAndAgentCounters:
    def test_tool_calls_and_failures(self):
        metrics = Metrics()
        metrics.observe_tool_call(tool="erp_purchase_analysis", success=True)
        metrics.observe_tool_call(
            tool="erp_purchase_analysis", success=False, permission_denied=True
        )
        snapshot = metrics.snapshot()
        assert snapshot["tool_call_count"] == 2
        assert snapshot["tool_error_count"] == 1
        assert snapshot["permission_denied_count"] == 1

    def test_agent_runs_are_grouped_by_status(self):
        metrics = Metrics()
        metrics.observe_agent_run(status="completed")
        metrics.observe_agent_run(status="completed")
        metrics.observe_agent_run(status="max_steps")
        snapshot = metrics.snapshot()
        assert snapshot["agent_run_count"] == 3
        assert snapshot["agent_runs_by_status"] == {"completed": 2, "max_steps": 1}

    def test_audit_writes_are_counted(self):
        metrics = Metrics()
        metrics.observe_audit_write()
        assert metrics.snapshot()["audit_write_count"] == 1


class TestLifecycle:
    def test_reset_clears_everything(self):
        metrics = Metrics()
        metrics.observe_request(
            endpoint="GET /health", status_code=500, latency_ms=5, error_code="INTERNAL_ERROR"
        )
        metrics.observe_tool_call(tool="knowledge_search", success=False)
        metrics.reset()
        snapshot = metrics.snapshot()
        assert snapshot["request_count"] == 0
        assert snapshot["tool_call_count"] == 0
        assert snapshot["error_by_code"] == {}

    def test_simple_counters_are_exposed_as_properties(self):
        metrics = Metrics()
        metrics.observe_request(endpoint="GET /metrics", status_code=200, latency_ms=1)
        metrics.observe_tool_call(tool="x", success=True)
        assert metrics.request_count == 1
        assert metrics.tool_call_count == 1

    def test_snapshot_is_json_serialisable(self):
        import json

        metrics = Metrics()
        metrics.observe_request(endpoint="GET /health", status_code=200, latency_ms=1.5)
        assert json.loads(json.dumps(metrics.snapshot()))["avg_latency_ms"] == 1.5
