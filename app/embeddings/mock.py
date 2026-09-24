"""MockEmbeddingProvider: deterministic hashed embeddings so RAG runs offline.

No network, no model download, no API key. Text is turned into a bag of
CJK character n-grams plus latin/number tokens, hashed into a fixed number of
buckets and L2-normalised, so lexically similar texts get a high cosine
similarity. Good enough to exercise the whole RAG pipeline in tests and demos.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.embeddings.base import BaseEmbeddingProvider

_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    """CJK character bigrams (plus lone characters) and lowercase latin/digit words.

    Bigrams only: single Chinese characters are so frequent that including them
    makes every pair of documents look similar, which buries the real matches.
    """
    tokens: list[str] = []
    lowered = text.lower()
    for run in _CJK_RUN_RE.findall(lowered):
        if len(run) == 1:
            tokens.append(run)
            continue
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
    tokens.extend(_TOKEN_RE.findall(lowered))
    return tokens


def hash_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic hashed bag-of-ngrams embedding, L2-normalised."""
    vec = [0.0] * dimensions
    for token in _tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest, "big") % dimensions
        # Every token contributes +1; collisions simply add up.
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Offline embedding provider used by default and in all tests."""

    def __init__(self, dimensions: int = 1024) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self._dimensions = dimensions

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model(self) -> str:
        return "mock-embedding"

    async def _embed_impl(self, texts: list[str]) -> list[list[float]]:
        return [hash_embedding(text, self._dimensions) for text in texts]
