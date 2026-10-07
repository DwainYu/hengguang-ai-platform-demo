"""Integration tests for the Day-4 RBAC matrix (SPEC section 9).

These run the **real** authentication path: the module is marked ``real_auth`` so
the shared conftest does not inject the demo-admin identity for the Day-1..3
suites. Every behaviour listed in the Day-4 brief is asserted here:

1. no Authorization header -> 401
2. invalid token -> 401
3. operator: knowledge query -> allowed
4. operator: safety summary -> allowed
5. operator: ERP tool -> denied (403 at the tool boundary)
6. operator: audit read -> 403
7. manager: audit read -> allowed
8. manager: knowledge ingest -> 403
9. admin: knowledge ingest -> allowed
10. admin: all tools -> allowed
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.database import Database
from app.embeddings.mock import MockEmbeddingProvider
from app.main import app
from app.rag.store import VectorStore
from app.services.agent_service import AgentService, get_agent_service
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

pytestmark = pytest.mark.real_auth

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = REPO_ROOT / "data" / "documents"

ADMIN = {"Authorization": "Bearer demo-admin-token"}
MANAGER = {"Authorization": "Bearer demo-manager-token"}
OPERATOR = {"Authorization": "Bearer demo-operator-token"}

ERP_QUESTION = "最近30天主要原材料采购价格如何变化？"
SAFETY_QUESTION = "最近一个月哪个区域安全问题最多？"


@pytest.fixture
def service(tmp_path: Path) -> KnowledgeService:
    return KnowledgeService(
        store=VectorStore(path=tmp_path / "rbac-chroma", collection="rbac"),
        embeddings=MockEmbeddingProvider(),
        config=Settings(documents_dir=str(DOCUMENTS_DIR)),
    )


@pytest.fixture
def agent_service(service: KnowledgeService, seeded_database: Database) -> AgentService:
    return AgentService(knowledge_service=service, database=seeded_database)


@pytest.fixture
def client(service: KnowledgeService, agent_service: AgentService) -> TestClient:
    app.dependency_overrides[get_knowledge_service] = lambda: service
    app.dependency_overrides[get_agent_service] = lambda: agent_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_knowledge_service, None)
    app.dependency_overrides.pop(get_agent_service, None)


@pytest.fixture
def knowledge_base(client: TestClient) -> dict:
    response = client.post(
        "/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)}, headers=ADMIN
    )
    assert response.status_code == 200, response.text
    return response.json()


def tool_calls(response) -> list[dict]:
    return response.json()["tool_calls"]


class TestUnauthenticated:
    @pytest.mark.parametrize(
        ("method", "path", "payload"),
        [
            ("get", "/api/models", None),
            ("post", "/api/chat", {"message": "你好"}),
            ("post", "/api/agent/run", {"message": "你好"}),
            ("get", "/api/audit", None),
            ("get", "/api/users", None),
            ("post", "/api/knowledge/search", {"query": "恒光"}),
            ("get", "/api/knowledge/documents", None),
            ("post", "/api/knowledge/ingest", {"path": str(DOCUMENTS_DIR)}),
        ],
    )
    def test_missing_token_is_401_on_every_protected_endpoint(self, client, method, path, payload):
        response = client.request(method, path, json=payload)
        assert response.status_code == 401, response.text
        body = response.json()
        assert body["error"]["code"] == "UNAUTHENTICATED"
        assert body["request_id"].startswith("req_")
        assert body["detail"]

    def test_401_advertises_the_scheme_but_not_tokens(self, client):
        """401 response must show the auth scheme but must NOT leak demo tokens."""
        response = client.get("/api/audit")
        assert response.status_code == 401
        assert response.headers["www-authenticate"].startswith("Bearer")
        details = response.json()["error"]["details"]
        # Should list roles as hints, not actual tokens
        assert "demo_tokens" in details
        tokens_value = details["demo_tokens"]
        assert "admin" in tokens_value
        assert "manager" in tokens_value
        assert "operator" in tokens_value
        # Must NOT contain any actual token strings
        for forbidden_token in ("demo-admin-token", "demo-manager-token", "demo-operator-token"):
            assert forbidden_token not in tokens_value

    @pytest.mark.parametrize(
        "header", ["Bearer nope", "Token demo-admin-token", "Bearer", "Bearer "]
    )
    def test_invalid_token_is_401_never_500(self, client, header):
        response = client.get("/api/models", headers={"Authorization": header})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"

    def test_health_and_metrics_do_not_need_a_token(self, client):
        assert client.get("/health").status_code == 200
        assert client.get("/metrics").status_code == 200

    def test_errors_never_leak_a_traceback_or_a_credential(self, client):
        body = client.get("/api/audit").text.lower()
        for forbidden in ("traceback", 'file "', "sqlite", "password", "authorization:"):
            assert forbidden not in body


class TestOperator:
    def test_knowledge_query_is_allowed(self, client, knowledge_base):
        response = client.post(
            "/api/knowledge/search", json={"query": "恒光主要有哪些业务？"}, headers=OPERATOR
        )
        assert response.status_code == 200, response.text
        assert response.json()["count"] >= 1

    def test_safety_summary_via_agent_is_allowed(self, client):
        response = client.post(
            "/api/agent/run", json={"message": SAFETY_QUESTION}, headers=OPERATOR
        )
        assert response.status_code == 200, response.text
        calls = tool_calls(response)
        assert [call["name"] for call in calls] == ["safety_incident_analysis"]
        assert calls[0]["success"] is True
        assert "安全" in response.json()["answer"]

    def test_erp_tool_is_denied_for_operator(self, client):
        response = client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=OPERATOR)
        assert response.status_code == 200, response.text
        (call,) = tool_calls(response)
        assert call["name"] == "erp_purchase_analysis"
        assert call["success"] is False
        assert call["error_code"] == "PERMISSION_DENIED"
        assert "权限" in response.json()["answer"]
        assert response.json()["role"] == "operator"

    def test_audit_read_is_403(self, client):
        response = client.get("/api/audit", headers=OPERATOR)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "PERMISSION_DENIED"
        assert response.json()["error"]["details"]["required_permission"] == "audit:read"

    def test_ingest_is_403(self, client):
        response = client.post(
            "/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)}, headers=OPERATOR
        )
        assert response.status_code == 403

    def test_models_and_users_are_403(self, client):
        assert client.get("/api/models", headers=OPERATOR).status_code == 403
        assert client.get("/api/users", headers=OPERATOR).status_code == 403


class TestManager:
    def test_audit_read_is_allowed(self, client, knowledge_base):
        response = client.get("/api/audit", headers=MANAGER)
        assert response.status_code == 200, response.text
        assert response.json()["viewer"]["role"] == "manager"

    def test_ingest_is_403(self, client):
        response = client.post(
            "/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)}, headers=MANAGER
        )
        assert response.status_code == 403
        assert "knowledge:ingest" in response.json()["error"]["details"]["required_permission"]

    def test_erp_and_safety_tools_are_allowed(self, client):
        for question, expected in (
            (ERP_QUESTION, "erp_purchase_analysis"),
            (SAFETY_QUESTION, "safety_incident_analysis"),
        ):
            response = client.post("/api/agent/run", json={"message": question}, headers=MANAGER)
            assert response.status_code == 200, response.text
            (call,) = tool_calls(response)
            assert call["name"] == expected
            assert call["success"] is True, call["error"]

    def test_user_management_is_403(self, client):
        assert client.get("/api/users", headers=MANAGER).status_code == 403


class TestAdmin:
    def test_ingest_is_allowed(self, client, knowledge_base):
        assert knowledge_base["documents"] >= 4

    def test_all_endpoints_answer(self, client, knowledge_base):
        assert client.get("/api/models", headers=ADMIN).status_code == 200
        assert client.get("/api/audit", headers=ADMIN).status_code == 200
        assert client.get("/api/users", headers=ADMIN).status_code == 200
        assert client.post("/api/chat", json={"message": "你好"}, headers=ADMIN).status_code == 200

    def test_all_four_tools_are_usable(self, client, knowledge_base):
        for question, expected in (
            (ERP_QUESTION, "erp_purchase_analysis"),
            (SAFETY_QUESTION, "safety_incident_analysis"),
            ("恒光主要有哪些业务？", "knowledge_search"),
            ("查看恒光2025年年报的详细信息", "document_lookup"),
        ):
            response = client.post("/api/agent/run", json={"message": question}, headers=ADMIN)
            assert response.status_code == 200, response.text
            assert tool_calls(response)[0]["name"] == expected
            assert tool_calls(response)[0]["success"] is True, tool_calls(response)[0]

    def test_models_endpoint_lists_tools_and_permissions(self, client):
        body = client.get("/api/models", headers=ADMIN).json()
        assert {model["kind"] for model in body["models"]} == {"chat", "embedding"}
        assert set(body["agent"]["allowed_tools"]) == set(body["agent"]["tools"])
        assert "audit:read" in body["permissions"]


class TestDeniedCallsAreAudited:
    def test_route_denial_is_audited_for_manager_ingest(
        self, client, seeded_database, knowledge_base
    ):
        response = client.post(
            "/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)}, headers=MANAGER
        )
        assert response.status_code == 403
        rows = seeded_database.query(
            "SELECT action, status FROM audit_logs WHERE request_id = :rid",
            {"rid": response.json()["request_id"]},
        )
        # The denial is filed under the same action as a successful ingest, so an
        # `action=knowledge.ingest` filter returns completions *and* refusals.
        assert {"action": "knowledge.ingest", "status": "denied"} in [dict(row) for row in rows]

    def test_denied_action_shares_the_namespace_of_success(self, client, seeded_database):
        """Route denials must not invent `permission:value` action names."""

        before = seeded_database.query(
            "SELECT COUNT(*) AS n FROM audit_logs WHERE action = 'knowledge.ingest'"
        )
        client.post("/api/knowledge/ingest", json={}, headers=MANAGER)
        after = seeded_database.query(
            "SELECT COUNT(*) AS n FROM audit_logs WHERE action = 'knowledge.ingest'"
        )
        assert int(after[0]["n"]) == int(before[0]["n"]) + 1
        leaked = seeded_database.query(
            "SELECT COUNT(*) AS n FROM audit_logs WHERE action = 'knowledge:ingest'"
        )
        assert int(leaked[0]["n"]) == 0

    def test_agent_tool_denial_writes_a_denied_row(self, client, audit_log, seeded_database):
        response = client.post("/api/agent/run", json={"message": ERP_QUESTION}, headers=OPERATOR)
        request_id = response.json()["request_id"]
        rows = seeded_database.query(
            "SELECT action, tool_name, status FROM audit_logs WHERE request_id = :rid ORDER BY id",
            {"rid": request_id},
        )
        assert {
            "action": "tool.call",
            "tool_name": "erp_purchase_analysis",
            "status": "denied",
        } in [dict(r) for r in rows]
        assert {"action": "agent.run", "tool_name": None, "status": "denied"} in [
            dict(r) for r in rows
        ]

    def test_successful_tool_calls_also_produce_rows(self, client, seeded_database):
        response = client.post(
            "/api/agent/run", json={"message": SAFETY_QUESTION}, headers=OPERATOR
        )
        request_id = response.json()["request_id"]
        rows = seeded_database.query(
            "SELECT tool_name, status FROM audit_logs WHERE request_id = :rid", {"rid": request_id}
        )
        assert {"tool_name": "safety_incident_analysis", "status": "success"} in [
            dict(row) for row in rows
        ]
