"""ModelProvider / ModelResponse / ToolCall protocol definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolCall:
    """A tool invocation requested by the model (OpenAI tool-call format)."""

    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class ModelResponse:
    """Standardized response from any model provider.

    ``tool_calls`` is empty for plain text responses; a non-empty list means
    the model wants tools executed before it can answer (Day 3).
    """

    content: str
    model: str
    provider: str
    usage: dict | None = None
    latency_ms: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)


@runtime_checkable
class ModelProvider(Protocol):
    """Protocol for LLM providers.

    Business code MUST depend only on this protocol, never on concrete
    provider implementations.
    """

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float = 0.2,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
    ) -> ModelResponse: ...


class BaseProvider(ABC):
    """Abstract base class with common logic for providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def _chat_impl(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float,
        response_format: dict | None,
        tools: list[dict] | None,
    ) -> ModelResponse: ...

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float = 0.2,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
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
            tools=tools,
        )
