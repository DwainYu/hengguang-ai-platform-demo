"""OpenAI-compatible embedding provider via httpx (text-embedding-3 / bge / Ollama)."""

from __future__ import annotations

from typing import Any

import httpx

from app.embeddings.base import BaseEmbeddingProvider


class OpenAICompatibleEmbeddingProvider(BaseEmbeddingProvider):
    """Provider for any OpenAI-compatible ``POST /embeddings`` endpoint.

    Works with OpenAI, DashScope/Qwen compatible mode, SiliconFlow, and Ollama's
    OpenAI-compatible endpoint. Never used by the test suite: tests run offline
    against :class:`~app.embeddings.mock.MockEmbeddingProvider`.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        dimensions: int = 0,
        batch_size: int = 32,
        timeout: float = 60.0,
    ) -> None:
        if not base_url:
            raise ValueError("EMBEDDING_BASE_URL is required for a non-mock provider")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions  # 0 = adopt whatever the API returns
        self._batch_size = max(1, batch_size)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def provider_name(self) -> str:
        if (
            "ollama" in self._base_url
            or "localhost" in self._base_url
            or "127.0.0.1" in self._base_url
        ):
            return "ollama"
        if "dashscope" in self._base_url:
            return "qwen"
        return "openai-compatible"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model(self) -> str:
        return self._model

    async def _embed_impl(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors.extend(await self._embed_batch(batch))
        return vectors

    async def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        payload: dict[str, Any] = {"model": self._model, "input": batch}
        if self._dimensions:
            payload["dimensions"] = self._dimensions

        resp = await self._client.post(f"{self._base_url}/embeddings", json=payload)
        resp.raise_for_status()
        data = resp.json()

        items = sorted(data["data"], key=lambda item: item.get("index", 0))
        vectors = [item["embedding"] for item in items]
        if vectors and not self._dimensions:
            self._dimensions = len(vectors[0])
        return vectors

    async def close(self) -> None:
        await self._client.aclose()
