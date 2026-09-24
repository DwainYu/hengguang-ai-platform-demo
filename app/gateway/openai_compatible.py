"""OpenAI-compatible provider (DeepSeek / Qwen / Ollama) via httpx."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.gateway.base import BaseProvider, ModelResponse, ToolCall


def parse_tool_calls(raw: object, *, fallback_prefix: str = "call") -> list[ToolCall]:
    """Parse OpenAI-format ``tool_calls`` into ToolCall objects.

    Tolerates missing ids/names and malformed JSON arguments: the agent loop's
    argument validation turns those into controlled ToolResult failures.
    """
    calls: list[ToolCall] = []
    for index, item in enumerate(raw or [], start=1):
        if not isinstance(item, dict):
            continue
        function = item.get("function") or {}
        name = str(function.get("name") or "").strip()
        if not name:
            continue
        raw_arguments = function.get("arguments")
        if isinstance(raw_arguments, str) and raw_arguments.strip():
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {}
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
        else:
            arguments = {}
        calls.append(
            ToolCall(
                id=str(item.get("id") or f"{fallback_prefix}_{index}"),
                name=name,
                arguments=arguments if isinstance(arguments, dict) else {},
            )
        )
    return calls


class OpenAICompatibleProvider(BaseProvider):
    """Provider for any OpenAI-compatible API endpoint.

    Supports DeepSeek, Qwen, Ollama (with OpenAI-compatible endpoint), etc.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        default_model: str,
        timeout: float = 60.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def provider_name(self) -> str:
        # Infer from base_url for display purposes
        if "deepseek" in self._base_url:
            return "deepseek"
        if "qwen" in self._base_url or "dashscope" in self._base_url:
            return "qwen"
        if (
            "ollama" in self._base_url
            or "localhost" in self._base_url
            or "127.0.0.1" in self._base_url
        ):
            return "ollama"
        return "openai-compatible"

    async def _chat_impl(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float,
        response_format: dict | None,
        tools: list[dict] | None = None,
    ) -> ModelResponse:
        start = time.perf_counter()

        payload: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = f"{self._base_url}/chat/completions"
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        latency_ms = int((time.perf_counter() - start) * 1000)

        # OpenAI-compatible response format: text and/or tool calls
        choice = data["choices"][0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        usage = data.get("usage")

        return ModelResponse(
            content=content,
            model=data.get("model", model or self._default_model),
            provider=self.provider_name,
            usage=usage,
            latency_ms=latency_ms,
            tool_calls=parse_tool_calls(message.get("tool_calls")),
        )

    async def close(self) -> None:
        await self._client.aclose()
