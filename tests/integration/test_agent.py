"""Integration tests for the Agent API (Day 3: POST /api/agent/run)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.embeddings.mock import MockEmbeddingProvider
from app.gateway.mock import MockProvider
from app.gateway.router import ModelGateway
from app.main import app
from app.rag.store import VectorStore
from app.services.agent_service import AgentService, get_agent_service
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = REPO_ROOT / "data" / "documents"


class UnavailableStore(VectorStore):
    """Store double that simulates Chroma being down."""

    def count(self) -> int:
        raise RuntimeError("Chroma unavailable")


def _agent_service(service: KnowledgeService, *, script: list[str] | None = None) -> AgentService:
    gateway = ModelGateway(providers={"mock": MockProvider(script=script)})
    return AgentService(
        knowledge_service=service,
        gateway=gateway,
        config=Settings(documents_dir=str(DOCUMENTS_DIR)),
    )


@pytest.fixture
def service(tmp_path: Path) -> KnowledgeService:
    """Knowledge service on a throw-away Chroma directory with mock embeddings."""
    return KnowledgeService(
        store=VectorStore(path=tmp_path / "chroma", collection="itest"),
        embeddings=MockEmbeddingProvider(),
        config=Settings(documents_dir=str(DOCUMENTS_DIR)),
    )


@pytest.fixture
def client(service: KnowledgeService):
    app.dependency_overrides[get_knowledge_service] = lambda: service
    app.dependency_overrides[get_agent_service] = lambda: _agent_service(service)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_knowledge_service, None)
    app.dependency_overrides.pop(get_agent_service, None)


@pytest.fixture
def ingested(client: TestClient) -> dict:
    response = client.post("/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)})
    assert response.status_code == 200, response.text
    return response.json()


class TestAgentRunEndpoint:
    """Day 3 acceptance: agent loop with tool calling, citations and safety limits."""

    def test_business_question_runs_knowledge_tool_with_citations(
        self, client: TestClient, ingested: dict
    ):
        response = client.post("/api/agent/run", json={"message": "恒光主要有哪些业务？"})
        assert response.status_code == 200, response.text
        body = response.json()

        assert body["request_id"].startswith("req_")
        assert body["answer"]
        assert body["model"] == "mock-model"
        assert body["provider"] == "mock"
        assert body["status"] == "completed"
        assert body["steps"] >= 2

        tool_calls = body["tool_calls"]
        assert len(tool_calls) >= 1
        assert tool_calls[0]["name"] == "knowledge_search"
        assert tool_calls[0]["arguments"]["query"] == "恒光主要有哪些业务？"
        assert tool_calls[0]["success"] is True

        sources = body["sources"]
        assert sources, "knowledge_search must keep sources"
        top = sources[0]
        for field in ("document_id", "title", "section", "source", "citation"):
            assert top[field], f"missing {field}"

        # RAG citation survives all the way into the final answer
        assert "[1]" in body["answer"]
        assert "引用来源" in body["answer"]

        trace = body["trace"]
        assert trace[0]["type"] == "llm"
        assert any(
            entry["type"] == "tool_call" and entry["tool"] == "knowledge_search" for entry in trace
        )
        assert trace[-1]["type"] == "final"

    def test_greeting_skips_tools(self, client: TestClient, ingested: dict):
        response = client.post("/api/agent/run", json={"message": "你好"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["answer"]
        assert body["tool_calls"] == []
        assert body["sources"] == []
        assert body["steps"] == 1
        assert body["status"] == "completed"

    def test_creative_request_does_not_fabricate_enterprise_facts(
        self, client: TestClient, ingested: dict
    ):
        response = client.post("/api/agent/run", json={"message": "帮我写一首诗"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["tool_calls"] == []
        assert "没有足够信息" in body["answer"]
        for forbidden in ("氯碱", "盐酸", "液碱", "净利润", "产能"):
            assert forbidden not in body["answer"]

    def test_enterprise_question_without_answer_still_searches(
        self, client: TestClient, ingested: dict
    ):
        """Scenario 3: 恒光-related but unknowable -> search, then honest answer."""
        response = client.post("/api/agent/run", json={"message": "恒光内部某员工今天几点下班？"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["tool_calls"][0]["name"] == "knowledge_search"
        assert body["status"] == "completed"

    def test_tool_failure_returns_controlled_result(self, service: KnowledgeService):
        broken = KnowledgeService(
            store=UnavailableStore(),
            embeddings=MockEmbeddingProvider(),
            config=Settings(documents_dir=str(DOCUMENTS_DIR)),
        )
        app.dependency_overrides[get_knowledge_service] = lambda: broken
        app.dependency_overrides[get_agent_service] = lambda: _agent_service(broken)
        try:
            with TestClient(app) as test_client:
                response = test_client.post(
                    "/api/agent/run", json={"message": "恒光主要有哪些业务？"}
                )
        finally:
            app.dependency_overrides.pop(get_knowledge_service, None)
            app.dependency_overrides.pop(get_agent_service, None)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "completed"
        tool_calls = body["tool_calls"]
        assert len(tool_calls) == 1
        assert tool_calls[0]["success"] is False
        assert "Chroma unavailable" in (tool_calls[0]["error"] or "")
        assert "工具执行失败" in body["answer"]

    def test_infinite_tool_call_loop_terminates(self, client: TestClient, ingested: dict):
        """Scripted provider always requests another tool: the loop must stop."""
        app.dependency_overrides[get_agent_service] = lambda: _agent_service(
            service, script=["knowledge_search"] * 20
        )
        try:
            with TestClient(app) as test_client:
                response = test_client.post(
                    "/api/agent/run",
                    json={"message": "恒光主要有哪些业务？", "max_steps": 5},
                )
        finally:
            app.dependency_overrides[get_agent_service] = lambda: _agent_service(service)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "max_steps"
        assert body["steps"] == 5
        assert len(body["tool_calls"]) == 5
        assert body["trace"][-1]["type"] != "final"
        assert "安全限制" in body["answer"]


class TestAgentRunValidation:
    def test_empty_message_is_rejected(self, client: TestClient, ingested: dict):
        assert client.post("/api/agent/run", json={"message": "  "}).status_code == 422

    def test_max_steps_bounds_are_enforced(self, client: TestClient, ingested: dict):
        too_low = client.post("/api/agent/run", json={"message": "你好", "max_steps": 0})
        too_high = client.post("/api/agent/run", json={"message": "你好", "max_steps": 99})
        assert too_low.status_code == 422
        assert too_high.status_code == 422
