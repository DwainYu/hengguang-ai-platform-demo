"""POST /api/chat — unified entry for chat/agent requests (Day 1+)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.router import gateway

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    mode: str = Field(default="auto", pattern="^(auto|chat|agent)$")
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    mode: str
    model: str
    provider: str
    latency_ms: int
    # For future Agent/RAG integration
    sources: list[dict] = []
    tool_calls: list[dict] = []


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint - routes to Model Gateway."""
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    start = time.perf_counter()

    messages = [
        {"role": "system", "content": "你是恒光 AI 平台助手，基于企业知识库回答问题。"},
        {"role": "user", "content": request.message},
    ]

    try:
        response = await gateway.chat(
            messages,
            model=request.model,
            temperature=request.temperature if request.temperature is not None else 0.2,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e}") from e

    latency_ms = int((time.perf_counter() - start) * 1000)

    return ChatResponse(
        request_id=request_id,
        answer=response.content,
        mode=request.mode,
        model=response.model,
        provider=response.provider,
        latency_ms=latency_ms,
    )
