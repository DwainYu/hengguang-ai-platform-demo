"""ModelProvider / ModelResponse protocol definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ModelResponse:
    """Standardized response from any model provider."""

    content: str
    model: str
    provider: str
    usage: dict | None = None
    latency_ms: int = 0


@runtime_checkable
class ModelProvider(Protocol):
    """Protocol for LLM providers.

    Business code MUST depend only on this protocol, never on concrete
    provider implementations.
    """

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float = 0.2,
        response_format: dict | None = None,
    ) -> ModelResponse: ...


class BaseProvider(ABC):
    """Abstract base class with common logic for providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def _chat_impl(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float,
        response_format: dict | None,
    ) -> ModelResponse: ...

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float = 0.2,
        response_format: dict | None = None,
    ) -> ModelResponse:
        """Public interface with basic validation."""
        if not messages:
            raise ValueError("messages cannot be empty")
        if temperature < 0 or temperature > 2:
            raise ValueError("temperature must be in [0, 2]")
        return await self._chat_impl(
            messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
        )
