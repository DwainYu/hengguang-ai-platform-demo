"""Knowledge endpoints: ingest, document listing and cited retrieval."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.rag.schemas import Citation, DocumentSummary
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_TOP_K = 20

KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]


class IngestRequest(BaseModel):
    """SPEC section 8.4: ingest everything below a path (default: DOCUMENTS_DIR)."""

    path: str | None = Field(default=None, description="Directory or single file to ingest")
    rebuild: bool = Field(default=False, description="Clear the collection before ingesting")


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    status: str
    skipped: list[str] = []
    errors: list[str] = []


class DocumentsResponse(BaseModel):
    """SPEC section 8.5: document list with chunk statistics."""

    documents: list[DocumentSummary]
    total_documents: int
    total_chunks: int


class SearchRequest(BaseModel):
    query: str = Field(default=..., min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=MAX_TOP_K)
    include_answer: bool = Field(
        default=True, description="Also generate a cited answer through the Model Gateway"
    )

    @field_validator("query")
    @classmethod
    def _strip_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query must not be blank")
        return cleaned


class SearchResult(BaseModel):
    """A retrieved chunk with the metadata a citation needs (SPEC section 6.3)."""

    chunk_id: str
    document_id: str
    title: str
    content: str
    score: float
    section: str | None = None
    page: int | None = None
    source: str
    url: str
    published_at: str
    position: int
    citation: str = Field(default="", description="Ready-to-use source label")


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]
    citations: list[Citation]
    answer: str | None = None
    model: str = ""
    provider: str = ""
    latency_ms: int


def _require_content(service: KnowledgeService) -> None:
    if service.store.count() == 0:
        raise HTTPException(
            status_code=409,
            detail="Knowledge base is empty; POST /api/knowledge/ingest first.",
        )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    service: KnowledgeServiceDep,
) -> IngestResponse:
    """Ingest public documents into the knowledge base.

    Admin-only access (SPEC sections 8.4 and 9) is enforced on Day 4 together
    with bearer tokens and the audit log; Day 2 keeps the endpoint open so the
    demo runs without authentication.
    """
    report = await service.ingest(request.path, rebuild=request.rebuild)
    return IngestResponse(
        documents=report.documents,
        chunks=report.chunks,
        status=report.status,
        skipped=report.skipped,
        errors=report.errors,
    )


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents(
    service: KnowledgeServiceDep,
) -> DocumentsResponse:
    """List ingested documents with chunk counts."""
    documents = service.list_documents()
    return DocumentsResponse(
        documents=documents,
        total_documents=len(documents),
        total_chunks=sum(document.chunks for document in documents),
    )


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    service: KnowledgeServiceDep,
) -> SearchResponse:
    """Retrieve top-K chunks with metadata + citation, and optionally answer."""
    _require_content(service)
    outcome = await service.search(
        request.query, top_k=request.top_k, include_answer=request.include_answer
    )
    # Results and citations come back in the same order, [1] == results[0].
    citations = outcome.citations
    return SearchResponse(
        query=outcome.query,
        count=len(outcome.results),
        results=[
            SearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                title=result.title,
                content=result.content,
                score=result.score,
                section=result.section,
                page=result.page,
                source=result.source,
                url=result.url,
                published_at=result.published_at,
                position=result.position,
                citation=citations[index].label,
            )
            for index, result in enumerate(outcome.results)
        ],
        citations=citations,
        answer=outcome.answer,
        model=outcome.model,
        provider=outcome.provider,
        latency_ms=outcome.latency_ms,
    )
