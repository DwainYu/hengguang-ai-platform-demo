"""Day 5 — the API contract the web console depends on (integration).

The console (`web/src/services/api.ts` + `web/src/types/index.ts`) is written
against the exact response fields of Day 1–4, so a renamed field would break the
UI silently while every backend test stayed green. These tests pin the contract
from the server side, on the real authentication path:

* the public endpoints the shell header polls (`/health`, `/metrics`);
* the key sets of `/api/models`, `/api/agent/run`, `/api/knowledge/*`,
  `/api/audit`, `/api/audit/{request_id}`, `/api/users`;
* role-scoped availability (operator must get 403 on `models:list` / `audit:read`,
  because the UI renders exactly that as "Permission denied");
* the controlled `PERMISSION_DENIED` tool outcome the trace panel renders as a
  badge — with no stack trace in the payload;
* the structured error envelope with its `request_id` (the UI shows it to users).

Nothing here weakens or changes behaviour: if a test fails, the API and the
console types have drifted apart.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

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

RAG_QUESTION = "恒光主要有哪些业务？"
ERP_QUESTION = "最近30天主要原材料采购价格有什么变化？"
SAFETY_QUESTION = "最近一个月哪个区域安全问题最多？"

HEALTH_KEYS = {"status", "version", "database", "request_count", "request_id"}
METRICS_KEYS = {
    "request_count",
    "success_count",
    "error_count",
    "avg_latency_ms",
    "max_latency_ms",
    "requests_by_status_class",
    "requests_by_endpoint",
    "error_by_code",
    "tool_call_count",
    "tool_error_count",
    "permission_denied_count",
    "agent_run_count",
    "agent_runs_by_status",
    "audit_write_count",
    "uptime_seconds",
    "app",
    "endpoint",
    "request_id",
}
TOOL_CALL_KEYS = {
    "name",
    "arguments",
    "success",
    "error",
    "error_code",
    "operation",
    "result_count",
}
TRACE_KEYS = {"step", "type", "tool", "latency_ms", "detail"}
SOURCE_KEYS = {
    "index",
    "document_id",
    "title",
    "section",
    "page",
    "source",
    "url",
    "score",
    "citation",
}
AUDIT_KEYS = {
    "id",
    "request_id",
    "user_id",
    "username",
    "role",
    "action",
    "endpoint",
    "operation",
    "tool",
    "model",
    "mode",
    "input_summary",
    "status",
    "latency_ms",
    "created_at",
}


@pytest.fixture
def service(tmp_path: Path) -> KnowledgeService:
    """A throw-away knowledge service (its own Chroma dir, mock embeddings)."""

    return KnowledgeService(
        store=VectorStore(path=tmp_path / "web-chroma", collection="web"),
        embeddings=MockEmbeddingProvider(),
        config=Settings(documents_dir=str(DOCUMENTS_DIR)),
    )


@pytest.fixture
def agent_service(service: KnowledgeService, seeded_database: Database) -> AgentService:
    return AgentService(knowledge_service=service, database=seeded_database)


@pytest.fixture
def console(agent_service: AgentService, service: KnowledgeService) -> Iterator[TestClient]:
    """Console-facing app wired to the throw-away services, real auth kept on."""

    app.dependency_overrides[get_knowledge_service] = lambda: service
    app.dependency_overrides[get_agent_service] = lambda: agent_service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_knowledge_service, None)
    app.dependency_overrides.pop(get_agent_service, None)


@pytest.fixture
def knowledge_base(console: TestClient) -> dict[str, Any]:
    """Ingest the public documents once so RAG-dependent assertions have data."""

    response = console.post("/api/knowledge/ingest", json={}, headers=ADMIN)
    assert response.status_code == 200, response.text
    return response.json()


def _keys(payload: dict[str, Any]) -> set[str]:
    return set(payload)


class TestPublicStatusEndpoints:
    """The shell header polls these with no token at all (no business data inside)."""

    def test_health_fields_the_dashboard_status_card_reads(self, console: TestClient) -> None:
        payload = console.get("/health").json()
        assert HEALTH_KEYS <= _keys(payload)
        assert payload["status"] == "ok"
        assert payload["request_id"].startswith("req_")
        assert {"configured", "initialized", "tables", "seeded", "rows"} <= _keys(
            payload["database"]
        )

    def test_metrics_has_the_counters_the_dashboard_cards_render(self, console: TestClient) -> None:
        payload = console.get("/metrics").json()
        assert METRICS_KEYS <= _keys(payload)
        assert set(payload["app"]) == {"version", "provider"}
        assert isinstance(payload["request_count"], int)

    def test_metrics_endpoint_labels_are_method_path(self, console: TestClient) -> None:
        console.get("/health")
        payload = console.get("/metrics").json()
        assert "GET /health" in payload["requests_by_endpoint"]
        assert set(payload["requests_by_endpoint"]["GET /health"]) == {"count", "avg_latency_ms"}

    def test_x_request_id_header_matches_the_body(self, console: TestClient) -> None:
        response = console.get("/health")
        assert response.headers["x-request-id"] == response.json()["request_id"]


class TestModelsContract:
    def test_models_body_matches_the_console_catalogue_types(self, console: TestClient) -> None:
        payload = console.get("/api/models", headers=MANAGER).json()
        assert {"request_id", "models", "agent", "permissions"} <= _keys(payload)
        assert payload["models"], "the console needs at least one chat model"
        for entry in payload["models"]:
            assert set(entry) == {"provider", "model", "available", "default", "kind"}
        assert {"chat", "embedding"} <= {entry["kind"] for entry in payload["models"]}
        assert set(payload["agent"]) == {"tools", "allowed_tools", "max_steps", "max_tool_calls"}
        assert payload["agent"]["max_steps"] >= 1
        assert payload["agent"]["max_tool_calls"] >= 1

    def test_tool_whitelist_is_the_four_shipped_tools(self, console: TestClient) -> None:
        tools = console.get("/api/models", headers=ADMIN).json()["agent"]["tools"]
        assert tools == [
            "knowledge_search",
            "document_lookup",
            "erp_purchase_analysis",
            "safety_incident_analysis",
        ]

    def test_allowed_tools_are_a_subset_of_the_whitelist(self, console: TestClient) -> None:
        agent = console.get("/api/models", headers=MANAGER).json()["agent"]
        assert "erp_purchase_analysis" in agent["allowed_tools"]
        assert set(agent["allowed_tools"]) <= set(agent["tools"])

    def test_models_reports_the_callers_own_permissions(self, console: TestClient) -> None:
        permissions = console.get("/api/models", headers=MANAGER).json()["permissions"]
        assert "models:list" in permissions
        assert "knowledge:ingest" not in permissions

    def test_models_never_serialises_a_credential(self, console: TestClient) -> None:
        text = console.get("/api/models", headers=ADMIN).text.lower()
        for forbidden in ("api_key", "authorization", "base_url", "sk-"):
            assert forbidden not in text


class TestAgentRunContract:
    def test_rag_run_shape_matches_console_types(self, console: TestClient) -> None:
        payload = console.post(
            "/api/agent/run", headers=MANAGER, json={"message": RAG_QUESTION}
        ).json()
        assert {
            "request_id",
            "answer",
            "model",
            "provider",
            "steps",
            "status",
            "latency_ms",
            "user",
            "role",
            "tool_calls",
            "sources",
            "trace",
        } <= _keys(payload)
        assert payload["status"] in {"completed", "max_steps", "max_tool_calls"}
        assert payload["role"] == "manager"
        assert payload["user"] == "manager_demo"
        for call in payload["tool_calls"]:
            assert _keys(call) == TOOL_CALL_KEYS
        for step in payload["trace"]:
            assert _keys(step) == TRACE_KEYS
            assert step["type"] in {"llm", "tool_call", "final", "stopped"}

    def test_cited_run_carries_every_source_field_the_ui_renders(
        self, console: TestClient, knowledge_base: dict[str, Any]
    ) -> None:
        payload = console.post(
            "/api/agent/run", headers=MANAGER, json={"message": RAG_QUESTION}
        ).json()
        assert payload["sources"], "RAG run must return citations"
        for source in payload["sources"]:
            assert _keys(source) == SOURCE_KEYS
            assert source["citation"]
            assert source["document_id"]

    def test_denied_tool_is_a_labeled_controlled_failure(self, console: TestClient) -> None:
        """The playground renders `error_code` as a badge: never a stack trace."""

        payload = console.post(
            "/api/agent/run", headers=OPERATOR, json={"message": ERP_QUESTION}
        ).json()
        assert payload["tool_calls"], "the ERP tool must have been attempted"
        (call,) = payload["tool_calls"]
        assert call["name"] == "erp_purchase_analysis"
        assert call["success"] is False
        assert call["error_code"] == "PERMISSION_DENIED"
        assert "Traceback" not in (call["error"] or "")
        assert payload["answer"], "the agent must still finish with a controlled answer"

    def test_safety_tool_is_allowed_for_operator(self, console: TestClient) -> None:
        payload = console.post(
            "/api/agent/run", headers=OPERATOR, json={"message": SAFETY_QUESTION}
        ).json()
        (call,) = payload["tool_calls"]
        assert call["name"] == "safety_incident_analysis"
        assert call["success"] is True
        assert call["operation"] == "incident_by_area"
        assert call["result_count"] >= 1

    def test_trace_pairs_tool_calls_in_order(self, console: TestClient) -> None:
        """The UI pairs the k-th `tool_call` trace entry with the k-th tool call."""

        payload = console.post(
            "/api/agent/run", headers=MANAGER, json={"message": ERP_QUESTION}
        ).json()
        tool_entries = [step for step in payload["trace"] if step["type"] == "tool_call"]
        assert [step["tool"] for step in tool_entries] == [
            call["name"] for call in payload["tool_calls"]
        ]


class TestKnowledgeContract:
    def test_documents_listing_matches_the_console_table(
        self, console: TestClient, knowledge_base: dict[str, Any]
    ) -> None:
        payload = console.get("/api/knowledge/documents", headers=OPERATOR).json()
        assert _keys(payload) == {"request_id", "documents", "total_documents", "total_chunks"}
        assert (
            payload["total_documents"] == len(payload["documents"]) == knowledge_base["documents"]
        )
        for document in payload["documents"]:
            assert set(document) == {
                "document_id",
                "title",
                "source",
                "url",
                "published_at",
                "chunks",
                "chars",
                "sections",
            }

    def test_search_returns_results_citations_and_answer(
        self, console: TestClient, knowledge_base: dict[str, Any]
    ) -> None:
        payload = console.post(
            "/api/knowledge/search",
            headers=MANAGER,
            json={"query": RAG_QUESTION, "top_k": 3, "include_answer": True},
        ).json()
        assert {
            "request_id",
            "query",
            "count",
            "results",
            "citations",
            "answer",
            "model",
            "provider",
            "latency_ms",
        } <= _keys(payload)
        assert payload["count"] == len(payload["results"])
        for result in payload["results"]:
            assert {
                "chunk_id",
                "document_id",
                "title",
                "content",
                "score",
                "section",
                "page",
                "source",
                "url",
                "published_at",
                "position",
                "citation",
            } <= _keys(result)
        assert payload["citations"], "the Knowledge page renders citation labels"
        assert payload["answer"]

    def test_search_without_answer_keeps_citations(
        self, console: TestClient, knowledge_base: dict[str, Any]
    ) -> None:
        payload = console.post(
            "/api/knowledge/search",
            headers=OPERATOR,
            json={"query": RAG_QUESTION, "include_answer": False},
        ).json()
        assert payload["answer"] is None
        assert payload["citations"]

    def test_empty_collection_answers_conflict_not_crash(self, console: TestClient) -> None:
        """The UI maps this 409 to "Knowledge base is not ready"."""

        response = console.post(
            "/api/knowledge/search", headers=MANAGER, json={"query": "任意问题"}
        )
        assert response.status_code == 409
        body = response.json()
        assert body["error"]["code"] == "CONFLICT"
        assert body["request_id"]

    def test_ingest_is_admin_only_and_reports_counts(self, console: TestClient) -> None:
        for headers, expected in ((OPERATOR, 403), (MANAGER, 403)):
            assert (
                console.post("/api/knowledge/ingest", headers=headers, json={}).status_code
                == expected
            )
        payload = console.post("/api/knowledge/ingest", headers=ADMIN, json={}).json()
        assert _keys(payload) == {
            "request_id",
            "documents",
            "chunks",
            "status",
            "skipped",
            "errors",
        }
        assert payload["documents"] > 0 and payload["chunks"] > 0


class TestAuditContract:
    def test_list_shape_paging_and_viewer(self, console: TestClient) -> None:
        console.post("/api/agent/run", headers=MANAGER, json={"message": RAG_QUESTION})
        payload = console.get("/api/audit?page=1&page_size=5", headers=MANAGER).json()
        assert {"items", "page", "page_size", "total", "request_id", "viewer"} <= _keys(payload)
        assert len(payload["items"]) <= 5
        assert payload["viewer"] == {"username": "manager_demo", "role": "manager"}
        for entry in payload["items"]:
            assert _keys(entry) == AUDIT_KEYS
            assert entry["created_at"]

    def test_filters_the_ui_dropdowns_use(self, console: TestClient) -> None:
        console.post("/api/agent/run", headers=MANAGER, json={"message": RAG_QUESTION})
        by_tool = console.get("/api/audit?tool=knowledge_search", headers=MANAGER).json()
        assert by_tool["items"]
        assert {entry["tool"] for entry in by_tool["items"]} == {"knowledge_search"}
        by_status = console.get("/api/audit?status=success", headers=MANAGER).json()
        assert {entry["status"] for entry in by_status["items"]} == {"success"}

    def test_trace_of_one_request_id(self, console: TestClient) -> None:
        run = console.post("/api/agent/run", headers=MANAGER, json={"message": ERP_QUESTION}).json()
        payload = console.get(f"/api/audit/{run['request_id']}", headers=MANAGER).json()
        assert payload["query_request_id"] == run["request_id"]
        actions = [entry["action"] for entry in payload["items"]]
        assert "agent.run" in actions
        assert "tool.call" in actions
        assert {entry["request_id"] for entry in payload["items"]} == {run["request_id"]}

    def test_denied_tool_call_lands_in_the_trail(self, console: TestClient) -> None:
        run = console.post(
            "/api/agent/run", headers=OPERATOR, json={"message": ERP_QUESTION}
        ).json()
        payload = console.get(f"/api/audit/{run['request_id']}", headers=ADMIN).json()
        # Newest first: the agent.run row and the denied tool.call row share the id.
        by_action = {entry["action"]: entry for entry in payload["items"]}
        denied_call = by_action["tool.call"]
        assert denied_call["status"] == "denied"
        assert denied_call["tool"] == "erp_purchase_analysis"
        assert denied_call["input_summary"]["error_code"] == "PERMISSION_DENIED"
        assert set(denied_call["input_summary"]) <= {"operation", "days", "limit", "error_code"}
        assert by_action["agent.run"]["status"] == "denied", "越权运行在审计里可被单独筛出来"
        assert console.get("/api/audit?status=denied", headers=ADMIN).json()["items"]

    def test_unknown_request_id_is_a_404_envelope(self, console: TestClient) -> None:
        response = console.get("/api/audit/req_not_in_the_database", headers=ADMIN)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    def test_operator_is_denied_with_a_renderable_envelope(self, console: TestClient) -> None:
        response = console.get("/api/audit", headers=OPERATOR)
        assert response.status_code == 403
        body = response.json()
        assert body["error"]["code"] == "PERMISSION_DENIED"
        assert body["error"]["details"]["required_permission"] == "audit:read"
        assert body["request_id"]

    def test_models_is_403_for_operator(self, console: TestClient) -> None:
        response = console.get("/api/models", headers=OPERATOR)
        assert response.status_code == 403
        assert response.json()["error"]["details"]["required_permission"] == "models:list"


class TestUsersContract:
    def test_directory_shape_used_by_settings(self, console: TestClient) -> None:
        payload = console.get("/api/users", headers=ADMIN).json()
        assert _keys(payload) == {"request_id", "users", "permission_roles"}
        assert len(payload["users"]) == 3
        for entry in payload["users"]:
            assert set(entry) == {"id", "username", "role", "permissions"}
        assert payload["permission_roles"]["knowledge:ingest"] == ["admin"]

    def test_directory_is_admin_only(self, console: TestClient) -> None:
        assert console.get("/api/users", headers=MANAGER).status_code == 403
        assert console.get("/api/users", headers=OPERATOR).status_code == 403


class TestValidationEnvelope:
    def test_blank_message_is_422_with_machine_code(self, console: TestClient) -> None:
        response = console.post("/api/agent/run", headers=MANAGER, json={"message": "   "})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_missing_token_is_401_on_a_console_endpoint(self, console: TestClient) -> None:
        response = console.post("/api/agent/run", json={"message": RAG_QUESTION})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"
