"""POST /api/chat — unified chat entry (Day 1) with Day-4 RBAC, audit and metrics.

The chat path still goes straight through the Model Gateway (Day-1 behaviour);
what Day 4 adds around it is the bearer-token check (``chat:run``), one audit row
per request with a *non-sensitive* summary (message length, never the text) and a
structured error when the provider fails.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.errors import ProviderError
from app.auth.auth import CurrentUser
from app.auth.dependencies import require
from app.auth.permissions import Permission
from app.gateway.base import ModelResponse
from app.gateway.router import gateway
from app.observability.audit import Actor, AuditAction, AuditLog, AuditStatus, get_audit_log
from app.observability.middleware import request_id_of

router = APIRouter(prefix="/api", tags=["chat"])

SYSTEM_PROMPT = "你是恒光 AI 平台助手，基于企业知识库回答问题。"

ChatUserDep = Annotated[CurrentUser, Depends(require(Permission.CHAT_RUN))]
RequestIdDep = Annotated[str, Depends(request_id_of)]
AuditLogDep = Annotated[AuditLog, Depends(get_audit_log)]


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
    user: str = ""
    role: str = ""
    sources: list[dict] = []
    tool_calls: list[dict] = []


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    request_id: RequestIdDep,
    user: ChatUserDep,
    audit: AuditLogDep,
) -> ChatResponse:
    """Chat through the Model Gateway (agent loop lives on /api/agent/run)."""

    started = time.perf_counter()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": payload.message},
    ]
    try:
        response: ModelResponse = await gateway.chat(
            messages,
            model=payload.model,
            temperature=payload.temperature if payload.temperature is not None else 0.2,
        )
    except Exception as error:  # provider failure stays a controlled 502
        latency_ms = int((time.perf_counter() - started) * 1000)
        audit.record_api(
            Actor.from_user(user, request_id),
            action=AuditAction.CHAT_COMPLETE,
            status=AuditStatus.ERROR,
            endpoint="POST /api/chat",
            request_id=request_id,
            mode=payload.mode,
            input_summary={"chars": len(payload.message), "error_type": type(error).__name__},
            latency_ms=latency_ms,
        )
        raise ProviderError(
            "模型服务暂时不可用，请稍后重试。",
            details={"error_type": type(error).__name__},
        ) from error

    latency_ms = int((time.perf_counter() - started) * 1000)
    status = AuditStatus.SUCCESS
    audit.record_api(
        Actor.from_user(user, request_id),
        action=AuditAction.CHAT_COMPLETE,
        status=status,
        endpoint="POST /api/chat",
        request_id=request_id,
        model_name=response.model,
        mode=payload.mode,
        input_summary={"chars": len(payload.message)},
        latency_ms=latency_ms,
    )
    return ChatResponse(
        request_id=request_id,
        answer=response.content,
        mode=payload.mode,
        model=response.model,
        provider=response.provider,
        latency_ms=latency_ms,
        user=user.username,
        role=user.role,
    )
