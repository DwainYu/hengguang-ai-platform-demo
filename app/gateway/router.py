"""ModelGateway: provider selection, fallback, error handling."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
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
        settings = get_settings()
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
        provider_name = name or get_settings().llm_provider
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
        """Chat with the configured provider, with optional fallback."""
        settings = get_settings()
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
            # Only fallback if configured and not already using mock
            if settings.llm_fallback and prov is not self._providers.get("mock"):
                mock_prov = self._providers.get("mock")
                if mock_prov:
                    import logging

                    logging.warning("provider fallback triggered: %s -> mock", prov.provider_name)
                    response = await mock_prov.chat(
                        messages,
                        model=model or settings.llm_model,
                        temperature=temperature,
                        response_format=response_format,
                        tools=tools,
                    )
                    return ModelResponse(
                        content=response.content,
                        model=response.model,
                        provider=response.provider,
                        usage=response.usage,
                        latency_ms=response.latency_ms,
                        tool_calls=response.tool_calls,
                        degraded=True,
                    )
            raise RuntimeError(f"Model provider error: {e}") from e

    def list_models(self) -> list[dict]:
        """Chat + embedding models that are actually usable, without any credential.

        ``available`` replaces the Day-1 ``enabled`` flag: it now means "this
        provider is registered and its model name is known", which is what the
        demo UI needs to build a model picker (§十四 GET /api/models).
        """

        settings = get_settings()
        active_provider = settings.llm_provider
        models: list[dict] = []
        for name, prov in self._providers.items():
            provider_name = getattr(prov, "provider_name", name)
            model_name = getattr(prov, "_default_model", "") or _fallback_model(provider_name)
            # A provider is the active default when LLM_PROVIDER matches either its
            # registration key or the display name it infers from its base URL.
            is_default = provider_name == active_provider or name == active_provider
            models.append(
                {
                    "provider": provider_name,
                    "model": model_name or "unknown",
                    "available": True,
                    "default": is_default,
                    "kind": "chat",
                }
            )
        models.append(
            {
                "provider": settings.embedding_provider,
                "model": settings.embedding_model or "mock-embedding",
                "available": True,
                "default": True,
                "kind": "embedding",
            }
        )
        return models


def _fallback_model(provider_name: str) -> str:
    """Model name to report when a provider does not expose a default model."""

    return "mock-model" if provider_name == "mock" else "unknown"


# Global gateway instance
gateway = ModelGateway()
