"""Unit tests for embedding providers (offline, no API key)."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.embeddings import build_embedding_provider
from app.embeddings.base import EmbeddingProvider, cosine_similarity
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider


class TestMockEmbeddingProvider:
    def test_implements_protocol(self):
        assert isinstance(MockEmbeddingProvider(), EmbeddingProvider)

    async def test_deterministic_and_normalised(self):
        provider = MockEmbeddingProvider(dimensions=128)
        first = await provider.embed_documents(["湖南恒光科技股份有限公司主营业务"])
        second = await provider.embed_documents(["湖南恒光科技股份有限公司主营业务"])
        assert first == second
        assert len(first[0]) == 128
        assert cosine_similarity(first[0], first[0]) == pytest.approx(1.0, abs=1e-6)

    async def test_embed_query_matches_embed_documents(self):
        provider = MockEmbeddingProvider(dimensions=128)
        query_vector = await provider.embed_query("氯酸钠的用途")
        document_vectors = await provider.embed_documents(["氯酸钠的用途"])
        assert query_vector == document_vectors[0]

    async def test_similar_texts_score_higher_than_unrelated(self):
        provider = MockEmbeddingProvider(dimensions=512)
        a, b, c = await provider.embed_documents(
            [
                "氯酸钠主要用于净水、造纸、医疗和冶金行业",
                "氯酸钠的用途包括造纸与水处理",
                "公司食堂提供早餐和午餐",
            ]
        )
        assert cosine_similarity(a, b) > cosine_similarity(a, c)

    async def test_empty_and_batch(self):
        provider = MockEmbeddingProvider(dimensions=64)
        assert await provider.embed_documents([]) == []
        vectors = await provider.embed_documents(["一", "二", "三"])
        assert len(vectors) == 3

    def test_rejects_bad_dimensions(self):
        with pytest.raises(ValueError):
            MockEmbeddingProvider(dimensions=0)


class TestProviderFactory:
    def test_default_settings_use_mock_offline(self):
        provider = build_embedding_provider(Settings(embedding_provider="mock"))
        assert provider.provider_name == "mock"
        assert provider.dimensions > 0

    def test_missing_base_url_falls_back_to_mock(self):
        provider = build_embedding_provider(
            Settings(embedding_provider="openai", embedding_base_url="", embedding_model="x")
        )
        assert provider.provider_name == "mock"

    def test_remote_provider_is_openai_compatible(self):
        provider = build_embedding_provider(
            Settings(
                embedding_provider="qwen",
                embedding_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                embedding_api_key="k",
                embedding_model="text-embedding-v3",
            )
        )
        assert isinstance(provider, OpenAICompatibleEmbeddingProvider)
        assert provider.provider_name == "qwen"
        # dimensions are taken from the API response, not forced by settings
        assert provider.dimensions == 0
