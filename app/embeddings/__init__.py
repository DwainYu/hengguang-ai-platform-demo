"""Embedding provider package.

`get_embedding_provider()` is the single access point (same idea as the Model
Gateway): business code never imports a concrete provider. Defaults to the
offline mock provider, so the platform runs with zero API keys.
"""

from __future__ import annotations

from app.config import Settings, settings
from app.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingProvider,
    cosine_similarity,
)
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "build_embedding_provider",
    "cosine_similarity",
    "get_embedding_provider",
    "reset_embedding_provider",
]


def build_embedding_provider(config: Settings | None = None) -> EmbeddingProvider:
    """Build the provider described by the settings, falling back to mock."""
    cfg = config or settings
    if cfg.embedding_provider == "mock" or not cfg.embedding_base_url:
        return MockEmbeddingProvider(dimensions=cfg.embedding_dimensions)
    # Remote providers define their own output size (dimensions == 0 = adopt it).
    return OpenAICompatibleEmbeddingProvider(
        base_url=cfg.embedding_base_url,
        api_key=cfg.embedding_api_key,
        model=cfg.embedding_model,
    )


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Process-wide embedding provider (lazily created from settings)."""
    global _provider
    if _provider is None:
        _provider = build_embedding_provider()
    return _provider


def set_embedding_provider(provider: EmbeddingProvider | None) -> None:
    """Override the process-wide provider (used by tests)."""
    global _provider
    _provider = provider


def reset_embedding_provider() -> None:
    set_embedding_provider(None)
