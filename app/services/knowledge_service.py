"""Knowledge service: wires embeddings + vector store + ingest + retrieval + RAG."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings, settings
from app.embeddings import EmbeddingProvider, get_embedding_provider
from app.rag.ingest import DocumentIngester, summarize_documents
from app.rag.pipeline import RagPipeline
from app.rag.retriever import Retriever
from app.rag.schemas import Citation, DocumentSummary, IngestReport, RetrievedChunk
from app.rag.store import VectorStore, get_vector_store


@dataclass
class SearchOutcome:
    """Everything `/api/knowledge/search` needs to return."""

    query: str
    results: list[RetrievedChunk]
    citations: list[Citation]
    answer: str | None
    model: str
    provider: str
    latency_ms: int


class KnowledgeService:
    """One object that owns the Day-2 RAG use cases.

    API endpoints depend on this class (via `get_knowledge_service`), so tests
    can point it at a temporary Chroma directory and the mock embedding
    provider without touching global settings.
    """

    def __init__(
        self,
        *,
        store: VectorStore | None = None,
        embeddings: EmbeddingProvider | None = None,
        config: Settings | None = None,
    ) -> None:
        self.config = config or settings
        self.embeddings = embeddings or get_embedding_provider()
        self.store = store or get_vector_store()
        self.ingester = DocumentIngester(
            store=self.store, embeddings=self.embeddings, config=self.config
        )
        self.retriever = Retriever(store=self.store, embeddings=self.embeddings, config=self.config)
        self.pipeline = RagPipeline(self.retriever, config=self.config)

    @property
    def documents_dir(self) -> Path:
        return Path(self.config.documents_dir)

    async def ingest(
        self, path: str | Path | None = None, *, rebuild: bool = False
    ) -> IngestReport:
        """Ingest a directory (defaults to `DOCUMENTS_DIR`) into Chroma."""
        root = Path(path) if path else self.documents_dir
        return await self.ingester.ingest_directory(root, rebuild=rebuild)

    def list_documents(self) -> list[DocumentSummary]:
        return summarize_documents(self.store)

    async def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        include_answer: bool = True,
    ) -> SearchOutcome:
        """Similarity search with citations, plus an optional cited answer."""
        started = time.perf_counter()
        if include_answer:
            # The pipeline retrieves once and cites the chunks it used.
            rag = await self.pipeline.answer(query, top_k=top_k)
            results, citations, answer = rag.results, rag.citations, rag.answer
            model, provider = rag.model, rag.provider
        else:
            results = await self.retriever.retrieve(query, top_k)
            citations = Retriever.build_citations(results)
            answer = None
            model = provider = ""
        return SearchOutcome(
            query=query,
            results=results,
            citations=citations,
            answer=answer,
            model=model,
            provider=provider,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


_service: KnowledgeService | None = None


def get_knowledge_service() -> KnowledgeService:
    """Process-wide knowledge service (built from settings on first use)."""
    global _service
    if _service is None:
        _service = KnowledgeService()
    return _service


def set_knowledge_service(service: KnowledgeService | None) -> None:
    """Override the service instance (used by tests and dependency injection)."""
    global _service
    _service = service
