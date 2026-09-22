"""Unit tests for Model Gateway."""

import pytest

from app.gateway.base import ModelProvider, ModelResponse
from app.gateway.mock import MockProvider
from app.gateway.openai_compatible import OpenAICompatibleProvider
from app.gateway.router import ModelGateway, gateway


class TestModelProviderProtocol:
    """Tests for the ModelProvider protocol."""

    def test_mock_provider_implements_protocol(self):
        """MockProvider should implement ModelProvider protocol."""
        provider = MockProvider()
        assert isinstance(provider, ModelProvider)

    def test_model_response_dataclass(self):
        """ModelResponse should be constructible with all fields."""
        resp = ModelResponse(
            content="test",
            model="test-model",
            provider="test",
            usage={"prompt": 10, "completion": 5},
            latency_ms=100,
        )
        assert resp.content == "test"
        assert resp.model == "test-model"
        assert resp.provider == "test"
        assert resp.usage == {"prompt": 10, "completion": 5}
        assert resp.latency_ms == 100


class TestMockProvider:
    """Tests for MockProvider."""

    @pytest.fixture
    def provider(self):
        return MockProvider()

    @pytest.mark.asyncio
    async def test_basic_response(self, provider):
        """MockProvider returns a response for any input."""
        resp = await provider.chat([{"role": "user", "content": "测试消息"}], model="mock-model")
        assert isinstance(resp, ModelResponse)
        assert resp.provider == "mock"
        assert resp.content
        assert resp.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_deterministic_responses(self, provider):
        """Same input should give deterministic response."""
        resp1 = await provider.chat(
            [{"role": "user", "content": "恒光主要有哪些业务？"}], model="mock-model"
        )
        resp2 = await provider.chat(
            [{"role": "user", "content": "恒光主要有哪些业务？"}], model="mock-model"
        )
        assert resp1.content == resp2.content

    @pytest.mark.asyncio
    async def test_hengguang_business_response(self, provider):
        """MockProvider has canned response for Hengguang business query."""
        resp = await provider.chat(
            [{"role": "user", "content": "恒光主要有哪些业务？"}], model="mock-model"
        )
        assert "无机精细化学品" in resp.content
        assert "氯碱" in resp.content

    @pytest.mark.asyncio
    async def test_purchase_price_response(self, provider):
        """MockProvider has canned response for purchase price query."""
        resp = await provider.chat(
            [{"role": "user", "content": "最近30天原材料采购价格有什么变化？"}], model="mock-model"
        )
        assert "盐酸" in resp.content
        assert "液碱" in resp.content

    @pytest.mark.asyncio
    async def test_safety_incident_response(self, provider):
        """MockProvider has canned response for safety query."""
        resp = await provider.chat(
            [{"role": "user", "content": "最近一个月哪个区域安全问题最多？"}], model="mock-model"
        )
        assert "A 车间" in resp.content

    @pytest.mark.asyncio
    async def test_validation_empty_messages(self, provider):
        """Empty messages should raise ValueError."""
        with pytest.raises(ValueError, match="messages cannot be empty"):
            await provider.chat([], model="mock-model")

    @pytest.mark.asyncio
    async def test_validation_temperature_bounds(self, provider):
        """Temperature out of bounds should raise ValueError."""
        with pytest.raises(ValueError, match="temperature must be in"):
            await provider.chat(
                [{"role": "user", "content": "test"}],
                model="mock-model",
                temperature=-0.1,
            )
        with pytest.raises(ValueError, match="temperature must be in"):
            await provider.chat(
                [{"role": "user", "content": "test"}],
                model="mock-model",
                temperature=2.1,
            )


class TestModelGateway:
    """Tests for ModelGateway."""

    def test_gateway_initialized(self):
        """Global gateway should be initialized."""
        assert isinstance(gateway, ModelGateway)

    def test_get_provider_mock(self):
        """Gateway should return mock provider by default."""
        provider = gateway.get_provider("mock")
        assert isinstance(provider, MockProvider)

    def test_get_provider_fallback(self):
        """Unknown provider should fallback to mock."""
        provider = gateway.get_provider("nonexistent")
        assert isinstance(provider, MockProvider)

    def test_list_models(self):
        """list_models should return at least mock model."""
        models = gateway.list_models()
        assert isinstance(models, list)
        assert len(models) >= 1
        assert any(m["provider"] == "mock" for m in models)

    @pytest.mark.asyncio
    async def test_chat_via_gateway(self):
        """Gateway.chat should work with mock provider."""
        resp = await gateway.chat([{"role": "user", "content": "测试"}], model="mock-model")
        assert isinstance(resp, ModelResponse)
        assert resp.provider == "mock"

    @pytest.mark.asyncio
    async def test_chat_with_explicit_provider(self):
        """Gateway.chat should respect explicit provider."""
        resp = await gateway.chat(
            [{"role": "user", "content": "测试"}],
            model="mock-model",
            provider="mock",
        )
        assert resp.provider == "mock"


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider (constructor only, no network)."""

    def test_construction(self):
        """Provider should construct with valid params."""
        provider = OpenAICompatibleProvider(
            base_url="https://api.example.com",
            api_key="test-key",
            default_model="test-model",
        )
        assert provider.provider_name in ("openai-compatible", "ollama")
        # Don't test actual HTTP calls here - they're integration tests
