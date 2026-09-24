"""Integration tests for the knowledge base API (Day 2: ingest / documents / search)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.embeddings.mock import MockEmbeddingProvider
from app.main import app
from app.rag.store import VectorStore
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = REPO_ROOT / "data" / "documents"


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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_knowledge_service, None)


@pytest.fixture
def ingested(client: TestClient) -> dict:
    response = client.post("/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)})
    assert response.status_code == 200, response.text
    return response.json()


class TestIngestEndpoint:
    def test_ingest_public_documents(self, client: TestClient, ingested: dict):
        assert ingested["status"] == "completed"
        assert ingested["documents"] >= 4
        assert ingested["chunks"] >= ingested["documents"]
        assert ingested["errors"] == []

    def test_ingest_is_idempotent(self, client: TestClient, ingested: dict):
        second = client.post("/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR)}).json()
        assert second["documents"] == ingested["documents"]
        assert second["chunks"] == ingested["chunks"]

    def test_ingest_rebuild_reports_same_size(self, client: TestClient, ingested: dict):
        rebuilt = client.post(
            "/api/knowledge/ingest", json={"path": str(DOCUMENTS_DIR), "rebuild": True}
        ).json()
        assert rebuilt["status"] == "completed"
        assert rebuilt["chunks"] == ingested["chunks"]

    def test_ingest_missing_path_fails_cleanly(self, client: TestClient):
        response = client.post("/api/knowledge/ingest", json={"path": "data/does-not-exist"})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed"
        assert body["documents"] == 0

    def test_ingest_default_path_uses_settings(self, service: KnowledgeService):
        report = service.ingester  # wiring check: default root comes from DOCUMENTS_DIR
        assert service.documents_dir == DOCUMENTS_DIR
        assert report is not None


class TestDocumentsEndpoint:
    def test_documents_listing_with_chunk_statistics(self, client: TestClient, ingested: dict):
        response = client.get("/api/knowledge/documents")
        assert response.status_code == 200
        body = response.json()
        assert body["total_documents"] == ingested["documents"]
        assert body["total_chunks"] == ingested["chunks"]
        by_id = {item["document_id"]: item for item in body["documents"]}
        profile = by_id["hengguang-public-profile"]
        assert profile["title"] == "湖南恒光科技股份有限公司公开简介"
        assert profile["chunks"] >= 3
        assert "主营业务" in profile["sections"]
        assert profile["url"].startswith("https://")

    def test_documents_empty_before_ingest(self, client: TestClient):
        response = client.get("/api/knowledge/documents")
        assert response.status_code == 200
        assert response.json()["documents"] == []


class TestSearchEndpoint:
    """Day 2 acceptance: KB-grounded answer + at least one source with title/section."""

    def test_business_question_returns_grounded_answer_and_citations(
        self, client: TestClient, ingested: dict
    ):
        response = client.post(
            "/api/knowledge/search",
            json={"query": "恒光主要有哪些业务？", "top_k": 3},
        )
        assert response.status_code == 200, response.text
        body = response.json()

        assert body["count"] >= 1
        top = body["results"][0]
        for field in ("document_id", "title", "content", "score", "section", "source"):
            assert top[field], f"missing {field}"
        assert top["section"] == "主营业务"
        assert "硫化工" in top["content"]

        citation = body["citations"][0]
        assert citation["index"] == 1
        assert citation["title"] == "湖南恒光科技股份有限公司公开简介"
        assert citation["section"] == "主营业务"

        assert body["answer"]
        assert "[1]" in body["answer"]
        assert "硫化工" in body["answer"]
        assert body["provider"] == "mock"
        assert body["latency_ms"] >= 0

    def test_search_without_answer_only_retrieves(self, client: TestClient, ingested: dict):
        body = client.post(
            "/api/knowledge/search",
            json={"query": "氯酸钠有什么用途", "top_k": 2, "include_answer": False},
        ).json()
        assert body["answer"] is None
        assert body["model"] == ""
        assert body["count"] == 2
        assert body["results"][0]["citation"].startswith("恒光股份主要产品")

    def test_search_respects_top_k(self, client: TestClient, ingested: dict):
        body = client.post(
            "/api/knowledge/search", json={"query": "营业收入 净利润", "top_k": 1}
        ).json()
        assert body["count"] == 1

    def test_search_before_ingest_conflicts(self, client: TestClient):
        response = client.post("/api/knowledge/search", json={"query": "恒光主要有哪些业务？"})
        assert response.status_code == 409
        assert "ingest" in response.json()["detail"]

    def test_irrelevant_question_reports_insufficient_information(
        self, client: TestClient, ingested: dict
    ):
        body = client.post("/api/knowledge/search", json={"query": "帮我写一首关于火锅的诗"}).json()
        assert body["count"] == 0
        assert body["results"] == []
        assert "没有足够信息" in body["answer"]

    @pytest.mark.parametrize("query", ["", "   ", "x" * 2001])
    def test_query_validation(self, client: TestClient, ingested: dict, query: str):
        assert client.post("/api/knowledge/search", json={"query": query}).status_code == 422

    def test_top_k_validation(self, client: TestClient, ingested: dict):
        assert (
            client.post("/api/knowledge/search", json={"query": "恒光", "top_k": 999}).status_code
            == 422
        )
