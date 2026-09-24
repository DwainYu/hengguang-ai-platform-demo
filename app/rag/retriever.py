"""Retriever: hybrid similarity search (vector + lexical overlap) with citations.

Chroma provides the semantic-recall part. Because the default embedding provider
is the offline hash-based mock, a cheap lexical signal is fused on top: the share
of query terms that literally appear in the chunk body and in its title / section
heading. With a real embedding provider the same fusion just acts as a modest
re-ranking bonus.
"""

from __future__ import annotations

import re

from app.config import Settings, settings
from app.embeddings import EmbeddingProvider
from app.rag.schemas import Citation, RetrievedChunk
from app.rag.store import VectorStore

# Fusion weights: vector similarity, term overlap in the chunk, term overlap in
# the document title / section heading (they add up to 1.0).
VECTOR_WEIGHT = 0.5
BODY_WEIGHT = 0.25
HEADER_WEIGHT = 0.25
# Over-fetch so the lexical signal can promote chunks the vector rank buried.
OVER_FETCH = 4
MAX_CANDIDATES = 200

_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def query_terms(query: str) -> set[str]:
    """Distinct CJK bigrams (plus lone characters) and latin/digit tokens."""
    terms: set[str] = set()
    lowered = query.lower()
    for run in _CJK_RUN_RE.findall(lowered):
        if len(run) == 1:
            terms.add(run)
            continue
        terms.update(run[index : index + 2] for index in range(len(run) - 1))
    terms.update(_WORD_RE.findall(lowered))
    return terms


def lexical_overlap(terms: set[str], haystack: str) -> float:
    """Fraction of the query terms that literally appear in ``haystack``."""
    if not terms:
        return 0.0
    lowered = haystack.lower()
    return sum(1 for term in terms if term in lowered) / len(terms)


class Retriever:
    """Turn a natural-language query into scored chunks with citation metadata."""

    def __init__(
        self,
        *,
        store: VectorStore,
        embeddings: EmbeddingProvider,
        config: Settings | None = None,
    ) -> None:
        cfg = config or settings
        self._store = store
        self._embeddings = embeddings
        self._top_k = cfg.rag_top_k
        self._min_score = cfg.rag_min_score

    @property
    def top_k(self) -> int:
        return self._top_k

    async def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Embed the query, search Chroma, fuse scores, attach citation metadata."""
        if not query.strip():
            return []
        limit = top_k or self._top_k
        embedding = await self._embeddings.embed_query(query)
        hits = self._store.query(embedding, min(limit * OVER_FETCH, MAX_CANDIDATES))

        terms = query_terms(query)
        scored: list[RetrievedChunk] = []
        for hit in hits:
            title = str(hit.metadata.get("title") or hit.metadata.get("document_id") or "")
            section = _optional_str(hit.metadata.get("section"))
            score = (
                VECTOR_WEIGHT * hit.score
                + BODY_WEIGHT * lexical_overlap(terms, hit.text)
                + HEADER_WEIGHT * lexical_overlap(terms, f"{title} {section or ''}")
            )
            scored.append(
                RetrievedChunk(
                    chunk_id=hit.chunk_id,
                    document_id=str(hit.metadata.get("document_id") or ""),
                    title=title,
                    content=hit.text,
                    score=round(score, 4),
                    section=section,
                    page=_optional_int(hit.metadata.get("page")),
                    source=str(hit.metadata.get("source") or "public"),
                    url=str(hit.metadata.get("url") or ""),
                    published_at=str(hit.metadata.get("published_at") or ""),
                    position=int(hit.metadata.get("position") or 0),
                )
            )
        scored.sort(key=lambda item: (-item.score, item.document_id, item.position))
        return [item for item in scored[:limit] if item.score >= self._min_score]

    @staticmethod
    def build_citations(results: list[RetrievedChunk]) -> list[Citation]:
        """Number the retrieved chunks so the answer can cite them as [1], [2] …"""
        return [Citation.from_result(item, index) for index, item in enumerate(results, start=1)]


def _optional_str(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        page = int(value)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return None
    return page if page > 0 else None
