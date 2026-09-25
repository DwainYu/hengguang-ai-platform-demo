"""Knowledge endpoints: ingest (admin), document listing and cited retrieval.

Day 4 adds the platform layer on top of the Day-2 RAG service: bearer-token RBAC
(``knowledge:ingest`` is admin-only, ``knowledge:query`` is shared), the request id
in every response, and one audit row per operation that records only compact,
non-sensitive summaries (never prompts or document text).
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.api.errors import ConflictError
from app.auth.auth import CurrentUser
from app.auth.dependencies import require
from app.auth.permissions import Permission
from app.observability.audit import Actor, AuditAction, AuditLog, AuditStatus, get_audit_log
from app.observability.middleware import request_id_of
from app.rag.schemas import Citation, DocumentSummary
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

MAX_TOP_K = 20

KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]
RequestIdDep = Annotated[str, Depends(request_id_of)]
AuditLogDep = Annotated[AuditLog, Depends(get_audit_log)]


class IngestRequest(BaseModel):
    """SPEC section 8.4: ingest everything below a path (default: DOCUMENTS_DIR)."""

    path: str | None = Field(default=None, description="Directory or single file to ingest")
    rebuild: bool = Field(default=False, description="Clear the collection before ingesting")


class IngestResponse(BaseModel):
    request_id: str = ""
    documents: int
    chunks: int
    status: str
    skipped: list[str] = []
    errors: list[str] = []


class DocumentsResponse(BaseModel):
    """SPEC section 8.5: document list with chunk statistics."""

    request_id: str = ""
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
    request_id: str = ""
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
        raise ConflictError(
            "知识库为空，请先调用 POST /api/knowledge/ingest。",
            details={"endpoint": "POST /api/knowledge/ingest"},
        )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    payload: IngestRequest,
    service: KnowledgeServiceDep,
    request_id: RequestIdDep,
    user: Annotated[CurrentUser, Depends(require(Permission.KNOWLEDGE_INGEST))],
    audit: AuditLogDep,
) -> IngestResponse:
    """Ingest public documents into the knowledge base (admin only, SPEC section 9)."""

    started = time.perf_counter()
    report = await service.ingest(payload.path, rebuild=payload.rebuild)
    status = AuditStatus.SUCCESS if report.status.startswith("completed") else AuditStatus.ERROR
    audit.record_api(
        Actor.from_user(user, request_id),
        action=AuditAction.KNOWLEDGE_INGEST,
        status=status,
        endpoint="POST /api/knowledge/ingest",
        request_id=request_id,
        input_summary={
            "path": payload.path or "default",
            "rebuild": payload.rebuild,
            "documents": report.documents,
            "chunk_count": report.chunks,
        },
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
    return IngestResponse(
        request_id=request_id,
        documents=report.documents,
        chunks=report.chunks,
        status=report.status,
        skipped=report.skipped,
        errors=report.errors,
    )


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents(
    service: KnowledgeServiceDep,
    request_id: RequestIdDep,
    user: Annotated[CurrentUser, Depends(require(Permission.KNOWLEDGE_QUERY))],
) -> DocumentsResponse:
    """List ingested documents with chunk counts."""

    documents = service.list_documents()
    return DocumentsResponse(
        request_id=request_id,
        documents=documents,
        total_documents=len(documents),
        total_chunks=sum(document.chunks for document in documents),
    )


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    payload: SearchRequest,
    service: KnowledgeServiceDep,
    request_id: RequestIdDep,
    user: Annotated[CurrentUser, Depends(require(Permission.KNOWLEDGE_QUERY))],
    audit: AuditLogDep,
) -> SearchResponse:
    """Retrieve top-K chunks with metadata + citation, and optionally answer."""

    started = time.perf_counter()
    _require_content(service)
    outcome = await service.search(
        payload.query, top_k=payload.top_k, include_answer=payload.include_answer
    )
    citations = outcome.citations
    audit.record_api(
        Actor.from_user(user, request_id),
        action=AuditAction.KNOWLEDGE_SEARCH,
        status=AuditStatus.SUCCESS,
        endpoint="POST /api/knowledge/search",
        request_id=request_id,
        model_name=outcome.model,
        mode="rag",
        input_summary={
            "top_k": payload.top_k or service.config.rag_top_k,
            "results": len(outcome.results),
        },
        latency_ms=outcome.latency_ms or int((time.perf_counter() - started) * 1000),
    )
    return SearchResponse(
        request_id=request_id,
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
