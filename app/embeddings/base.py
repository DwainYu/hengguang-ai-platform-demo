"""EmbeddingProvider protocol (embed_documents / embed_query).

Mirrors the Model Gateway design: business code depends on this protocol, never
on a concrete embedding implementation (SPEC section 2.3).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    @property
    def provider_name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class BaseEmbeddingProvider(ABC):
    """Common validation for embedding providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    async def _embed_impl(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and validate the returned vectors.

        ``dimensions == 0`` means "whatever the remote API returns"; local
        providers such as the mock one declare a fixed size.
        """
        cleaned = [t if t is not None else "" for t in texts]
        vectors = await self._embed_impl(cleaned)
        if len(vectors) != len(cleaned):
            raise RuntimeError(
                f"{self.provider_name} embedding provider returned "
                f"{len(vectors)} vectors for {len(cleaned)} inputs"
            )
        expected = self.dimensions
        for vec in vectors:
            if expected and len(vec) != expected:
                raise RuntimeError(
                    f"{self.provider_name}: expected {expected} dims, got {len(vec)}"
                )
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query text."""
        vectors = await self.embed_documents([text])
        return vectors[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity, 0.0 when either vector is all zeros."""
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
