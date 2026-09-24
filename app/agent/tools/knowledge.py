"""knowledge_search tool: Day-2 RAG retrieval wrapped as an agent tool.

The tool only converts arguments -> KnowledgeService -> ToolResult; retrieval,
citation and answer logic stay in ``app/rag`` + ``app/services``. The content
reuses the RAG context-block format (``app.rag.prompt``) so citations survive
all the way from Chroma through the agent into the final answer.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

from app.agent.tools.base import Tool, ToolResult
from app.rag.prompt import format_context
from app.services.knowledge_service import KnowledgeService


class KnowledgeSearchArgs(BaseModel):
    """Arguments for knowledge_search."""

    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


class KnowledgeSearchTool(Tool):
    """Search the enterprise knowledge base (public documents only)."""

    name = "knowledge_search"
    description = (
        "Search the Hengguang enterprise knowledge base (public documents: company "
        "profile, annual/half-year reports, news). Use this for any question about "
        "Hengguang's business, products, capacity, finance, safety or history. "
        "Returns numbered chunks with citations."
    )
    args_model = KnowledgeSearchArgs

    def __init__(self, knowledge_service: KnowledgeService) -> None:
        self._service = knowledge_service

    async def execute(self, arguments: dict) -> ToolResult:
        started = time.perf_counter()
        outcome = await self._service.search(
            arguments["query"], top_k=arguments["top_k"], include_answer=False
        )
        citations = outcome.citations
        sources = [
            {
                "index": citation.index,
                "document_id": result.document_id,
                "title": result.title,
                "section": result.section,
                "page": result.page,
                "source": result.source,
                "url": result.url,
                "score": result.score,
                "citation": citation.label,
            }
            for citation, result in zip(citations, outcome.results, strict=True)
        ]
        # Same numbered context block as the RAG pipeline: the model (or mock)
        # can cite it as [1], [2] … and empty results keep the explicit
        # "no information" message instead of an exception.
        content = format_context(outcome.results, citations)
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=content,
            metadata={
                "query": arguments["query"],
                "result_count": len(outcome.results),
                "sources": sources,
                "latency_ms": int((time.perf_counter() - started) * 1000),
            },
        )
