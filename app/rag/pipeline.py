"""RAG pipeline: retrieve -> build context -> LLM answer with citations.

The prompt contract (answer policy, context block) lives in
:mod:`app.rag.prompt` so that the Model Gateway and the pipeline agree on it.
All model access goes through `ModelGateway` (SPEC section 0.1 rule 3).
"""

from __future__ import annotations

import time

from app.config import Settings, settings
from app.gateway.base import ModelResponse
from app.gateway.router import ModelGateway
from app.gateway.router import gateway as default_gateway
from app.rag.prompt import build_messages
from app.rag.retriever import Retriever
from app.rag.schemas import Citation, RetrievedChunk


class RagAnswer:
    """Result of one grounded question: answer + retrieved chunks + citations."""

    def __init__(
        self,
        *,
        question: str,
        answer: str,
        results: list[RetrievedChunk],
        citations: list[Citation],
        model: str,
        provider: str,
        latency_ms: int,
    ) -> None:
        self.question = question
        self.answer = answer
        self.results = results
        self.citations = citations
        self.model = model
        self.provider = provider
        self.latency_ms = latency_ms

    @property
    def grounded(self) -> bool:
        """Whether the answer was based on retrieved knowledge-base content."""
        return bool(self.results)


class RagPipeline:
    """Question -> retrieve -> cited context -> Model Gateway -> answer."""

    def __init__(
        self,
        retriever: Retriever,
        *,
        gateway: ModelGateway | None = None,
        config: Settings | None = None,
    ) -> None:
        self._retriever = retriever
        self._gateway = gateway or default_gateway
        self._config = config or settings

    @property
    def retriever(self) -> Retriever:
        return self._retriever

    async def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Plain retrieval (used by the Day-3 knowledge tool)."""
        return await self._retriever.retrieve(question, top_k)

    async def answer(self, question: str, *, top_k: int | None = None) -> RagAnswer:
        """Retrieve context, then generate the answer through the gateway."""
        started = time.perf_counter()
        results = await self._retriever.retrieve(question, top_k)
        citations = Retriever.build_citations(results)
        model_result: ModelResponse = await self._gateway.chat(
            build_messages(question, results, citations),
            temperature=0.2,
        )
        return RagAnswer(
            question=question,
            answer=model_result.content,
            results=results,
            citations=citations,
            model=model_result.model,
            provider=model_result.provider,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
