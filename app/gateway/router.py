"""ModelGateway: provider selection, fallback, error handling."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.gateway.base import ModelProvider, ModelResponse
from app.gateway.mock import MockProvider
from app.gateway.openai_compatible import OpenAICompatibleProvider


class ModelGateway:
    """Unified gateway for all LLM interactions.

    Business code MUST use this gateway, never import providers directly.
    """

    def __init__(self, providers: dict[str, ModelProvider] | None = None) -> None:
        self._providers: dict[str, ModelProvider] = providers if providers is not None else {}
        if providers is None:
            self._init_providers()

    def _init_providers(self) -> None:
        """Initialize providers based on configuration."""
        # Always register mock provider (fallback)
        self._providers["mock"] = MockProvider()

        # Register real provider if configured
        if settings.llm_provider != "mock" and settings.llm_base_url and settings.llm_api_key:
            self._providers[settings.llm_provider] = OpenAICompatibleProvider(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                default_model=settings.llm_model,
            )

    def get_provider(self, name: str | None = None) -> ModelProvider:
        """Get a provider by name, or the default one."""
        provider_name = name or settings.llm_provider
        provider = self._providers.get(provider_name)
        if provider is None:
            # Fallback to mock if requested provider not available
            provider = self._providers.get("mock")
            if provider is None:
                raise RuntimeError("No model provider available")
        return provider

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.2,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
    ) -> ModelResponse:
        """Chat with the configured provider, with automatic fallback."""
        prov = self.get_provider(provider)
        try:
            return await prov.chat(
                messages,
                model=model or settings.llm_model,
                temperature=temperature,
                response_format=response_format,
                tools=tools,
            )
        except Exception as e:
            # Fallback to mock on failure if not already using mock
            if prov is not self._providers.get("mock"):
                mock_prov = self._providers.get("mock")
                if mock_prov:
                    return await mock_prov.chat(
                        messages,
                        model=model or settings.llm_model,
                        temperature=temperature,
                        response_format=response_format,
                        tools=tools,
                    )
            raise RuntimeError(f"Model provider error: {e}") from e

    def list_models(self) -> list[dict]:
        """List available models across all providers."""
        models = []
        for name, prov in self._providers.items():
            provider_name = getattr(prov, "provider_name", name)
            if hasattr(prov, "_default_model"):
                model_name = getattr(prov, "_default_model", "unknown")
            else:
                model_name = "mock-model"
            models.append(
                {
                    "provider": provider_name,
                    "model": model_name,
                    "enabled": True,
                }
            )
        return models


# Global gateway instance
gateway = ModelGateway()
