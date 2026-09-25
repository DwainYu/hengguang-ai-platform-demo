"""Integration tests for the Day-4 platform layer: request id, audit API, metrics,
structured errors and model listing.

RBAC itself is covered by ``test_rbac.py``; here we follow one request all the way
through ``User -> Auth -> API -> Agent -> Permission -> Tool -> Data -> Audit`` and
check that the observability surface (request_id, audit rows, metrics, structured
logs, error envelope) tells the same story.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.database import Database
from app.embeddings.mock import MockEmbeddingProvider
from app.main import app
from app.observability.logging import REQUEST_ID_HEADER
from app.rag.store import VectorStore
from app.services.agent_service import AgentService, get_agent_service
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

pytestmark = pytest.mark.real_auth

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = REPO_ROOT / "data" / "documents"

ADMIN = {"Authorization": "Bearer demo-admin-token"}
OPERATOR = {"Authorization": "Bearer demo-operator-token"}
ERP_QUESTION = "最近30天主要原材料采购价格如何变化？"


@pytest.fixture
def service(tmp_path: Path) -> KnowledgeService:
    return KnowledgeService(
        store=VectorStore(path=tmp_path / "platform-chroma", collection="platform"),
        embeddings=MockEmbeddingProvider(),
        config=Settings(documents_dir=str(DOCUMENTS_DIR)),
    )


@pytest.fixture
def client(service: KnowledgeService, seeded_database: Database, audit_log) -> TestClient:
    app.dependency_overrides[get_knowledge_service] = lambda: service
    app.dependency_overrides[get_agent_service] = lambda: AgentService(
        knowledge_service=service,
        database=seeded_database,
        audit=audit_log,
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_knowledge_service, None)
    app.dependency_overrides.pop(get_agent_service, None)


class TestRequestId:
    def test_every_response_carries_a_request_id(self, client):
        response = client.get("/health")
        assert response.headers[REQUEST_ID_HEADER].startswith("req_")
        assert client.get("/metrics").headers[REQUEST_ID_HEADER]

    def test_body_request_id_matches_the_header(self, client):
        response = client.get("/api/models", headers=ADMIN)
        assert response.json()["request_id"] == response.headers[REQUEST_ID_HEADER]

    def test_incoming_request_id_is_respected(self, client):
        response = client.get("/api/models", headers={**ADMIN, REQUEST_ID_HEADER: "req_mine_123"})
        assert response.json()["request_id"] == "req_mine_123"
        assert response.headers[REQUEST_ID_HEADER] == "req_mine_123"

    def test_one_agent_run_shares_one_request_id_everywhere(
        self, client, seeded_database, audit_log
    ):
        response = client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=ADMIN)
        assert response.status_code == 200, response.text
        request_id = response.json()["request_id"]

        rows = seeded_database.query(
            "SELECT action, tool_name, status, request_id FROM audit_logs WHERE request_id = :rid "
            "ORDER BY id",
            {"rid": request_id},
        )
        actions = [row["action"] for row in rows]
        assert "tool.call" in actions and "agent.run" in actions
        # HTTP → AgentRuntime → ToolExecutor → AuditLog all used the same id
        assert {row["request_id"] for row in rows} == {request_id}

    def test_error_responses_also_carry_the_id(self, client):
        response = client.get("/api/audit/req_does_not_exist", headers=ADMIN)
        assert response.status_code == 404
        assert response.json()["request_id"] == response.headers[REQUEST_ID_HEADER]


class TestAuditApi:
    def test_shape_is_items_page_page_size_total(self, client):
        response = client.get("/api/audit", headers=ADMIN, params={"page_size": 5})
        assert response.status_code == 200
        body = response.json()
        assert {"items", "page", "page_size", "total", "request_id"} <= set(body)
        assert body["page"] == 1 and body["page_size"] == 5
        assert len(body["items"]) <= 5

    def test_pagination_walks_the_whole_trail(self, client):
        for _ in range(6):
            client.get("/api/models", headers=ADMIN)
        first = client.get("/api/audit", headers=ADMIN, params={"page": 1, "page_size": 2}).json()
        second = client.get("/api/audit", headers=ADMIN, params={"page": 2, "page_size": 2}).json()
        assert first["total"] == second["total"]
        assert {item["id"] for item in first["items"]}.isdisjoint(
            {item["id"] for item in second["items"]}
        )

    def test_filter_by_tool(self, client):
        client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=ADMIN)
        body = client.get(
            "/api/audit", headers=ADMIN, params={"tool": "erp_purchase_analysis", "page_size": 50}
        ).json()
        assert body["total"] >= 1
        assert {item["tool"] for item in body["items"]} == {"erp_purchase_analysis"}

    def test_filter_by_status_denied(self, client):
        client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=OPERATOR)
        body = client.get(
            "/api/audit", headers=ADMIN, params={"status": "denied", "page_size": 50}
        ).json()
        assert body["items"]
        assert {item["status"] for item in body["items"]} == {"denied"}

    def test_lookup_by_request_id(self, client):
        request_id = client.post(
            "/api/agent/run", json={"message": ERP_QUESTION}, headers=ADMIN
        ).json()["request_id"]
        body = client.get(f"/api/audit/{request_id}", headers=ADMIN).json()
        assert body["query_request_id"] == request_id
        assert {item["request_id"] for item in body["items"]} == {request_id}

    def test_unknown_request_id_is_a_structured_404(self, client):
        response = client.get("/api/audit/req_nope", headers=ADMIN)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    def test_audit_rows_never_contain_credentials_or_prompts(self, client):
        client.post(
            "/api/agent/run",
            json={"message": "请把 demo-admin-token 和完整合同全文都记下来"},
            headers=ADMIN,
        )
        dump = json.dumps(
            client.get("/api/audit", headers=ADMIN, params={"page_size": 100}).json(),
            ensure_ascii=False,
        )
        for forbidden in ("demo-admin-token", "Authorization", "api_key", "合同全文"):
            assert forbidden not in dump

    def test_invalid_page_parameters_are_422(self, client):
        assert client.get("/api/audit", headers=ADMIN, params={"page": 0}).status_code == 422
        assert client.get("/api/audit", headers=ADMIN, params={"page_size": 500}).status_code == 422


class TestMetricsApi:
    def test_snapshot_has_the_required_counters(self, client):
        body = client.get("/metrics").json()
        assert {
            "request_count",
            "success_count",
            "error_count",
            "avg_latency_ms",
            "tool_call_count",
        } <= set(body)

    def test_counters_grow_with_traffic(self, client):
        before = client.get("/metrics").json()
        client.get("/api/models", headers=ADMIN)
        client.get("/api/models", headers=OPERATOR)  # 403
        after = client.get("/metrics").json()
        assert after["request_count"] >= before["request_count"] + 3
        assert after["error_count"] > before["error_count"]
        assert after["error_by_code"].get("PERMISSION_DENIED", 0) >= 1

    def test_tool_calls_are_counted(self, client):
        before = client.get("/metrics").json()["tool_call_count"]
        client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=ADMIN)
        assert client.get("/metrics").json()["tool_call_count"] > before

    def test_agent_runs_are_counted_by_status(self, client):
        client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=ADMIN)
        snapshot = client.get("/metrics").json()
        assert snapshot["agent_run_count"] >= 1
        assert "completed" in snapshot["agent_runs_by_status"]

    def test_metrics_is_json_not_prometheus_text(self, client):
        response = client.get("/metrics")
        assert response.headers["content-type"].startswith("application/json")


class TestStructuredErrors:
    def test_unknown_route_is_a_structured_404(self, client):
        response = client.get("/api/does-not-exist", headers=ADMIN)
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"
        assert "Traceback" not in response.text

    def test_validation_errors_are_structured(self, client):
        response = client.post("/api/agent/run", json={"message": ""}, headers=ADMIN)
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in body["error"]["details"]

    def test_tool_failure_does_not_become_a_500(self, client):
        response = client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=OPERATOR)
        assert response.status_code == 200
        assert response.json()["tool_calls"][0]["success"] is False

    def test_empty_database_search_is_a_structured_conflict(self, client):
        response = client.post("/api/knowledge/search", json={"query": "恒光"}, headers=ADMIN)
        assert response.status_code == 409
        body = response.json()
        assert body["error"]["code"] == "CONFLICT"
        assert "ingest" in body["detail"]


class TestModelsEndpoint:
    def test_lists_providers_without_any_secret(self, client):
        response = client.get("/api/models", headers=ADMIN)
        assert response.status_code == 200
        dump = json.dumps(response.json()).lower()
        for forbidden in ("api_key", "apikey", "authorization", "sk-"):
            assert forbidden not in dump

    def test_available_flag_is_present(self, client):
        models = client.get("/api/models", headers=ADMIN).json()["models"]
        assert models and all("available" in model and "provider" in model for model in models)


class TestStructuredLogging:
    def test_request_log_line_has_correlation_fields(self, client, caplog):
        with caplog.at_level("INFO", logger="app.observability.http"):
            response = client.get("/api/models", headers=ADMIN)
        line = next(
            record for record in caplog.records if getattr(record, "event", None) == "http.request"
        )
        assert line.request_id == response.json()["request_id"]
        assert line.endpoint == "GET /api/models"
        assert line.status == 200
        assert isinstance(line.latency_ms, float)

    def test_json_formatter_emits_one_object_per_line(self, client):
        import io
        import logging as std_logging

        from app.observability.logging import JsonFormatter

        stream = io.StringIO()
        handler = std_logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())
        logger = std_logging.getLogger("app.probe")
        logger.addHandler(handler)
        logger.propagate = False
        logger.info("probe", extra={"event": "probe", "tool": "erp_purchase_analysis"})
        payload = json.loads(stream.getvalue().strip())
        assert payload["event"] == "probe" and payload["tool"] == "erp_purchase_analysis"
        logger.removeHandler(handler)
