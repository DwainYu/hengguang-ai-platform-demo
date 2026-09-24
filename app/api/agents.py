"""POST /api/agent/run — Agent Runtime entry for tool-calling requests (Day 3)."""

from __future__ import annotations

import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.agent_service import AgentService, get_agent_service

router = APIRouter(prefix="/api/agent", tags=["agent"])

MAX_REQUEST_STEPS = 20

AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]


class AgentRunRequest(BaseModel):
    """One agent run: a user message plus optional loop-limit override."""

    message: str = Field(..., min_length=1, max_length=8000)
    max_steps: int | None = Field(default=None, ge=1, le=MAX_REQUEST_STEPS)

    @field_validator("message")
    @classmethod
    def _strip_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be blank")
        return cleaned


class AgentToolCallOut(BaseModel):
    """One executed tool call, with its outcome."""

    name: str
    arguments: dict = {}
    success: bool | None = None
    error: str | None = None


class AgentSourceOut(BaseModel):
    """A knowledge-base source that survived into the final answer (Day 2 -> 3)."""

    index: int | None = None
    document_id: str = ""
    title: str = ""
    section: str | None = None
    page: int | None = None
    source: str = ""
    url: str = ""
    score: float | None = None
    citation: str = Field(default="", description="Ready-to-use source label")


class AgentTraceOut(BaseModel):
    """One execution-trace entry."""

    step: int
    type: str
    tool: str | None = None
    latency_ms: int = 0
    detail: str | None = None


class AgentRunResponse(BaseModel):
    request_id: str
    answer: str
    model: str
    provider: str
    steps: int
    status: str = Field(description="completed | max_steps | max_tool_calls")
    latency_ms: int
    tool_calls: list[AgentToolCallOut] = []
    sources: list[AgentSourceOut] = []
    trace: list[AgentTraceOut] = []


@router.post("/run", response_model=AgentRunResponse)
async def agent_run(request: AgentRunRequest, service: AgentServiceDep) -> AgentRunResponse:
    """Run the agent loop: model -> tool call -> tools (RAG) -> final answer."""
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    started = time.perf_counter()
    try:
        result = await service.run(request.message, max_steps=request.max_steps)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}") from e
    latency_ms = int((time.perf_counter() - started) * 1000)

    return AgentRunResponse(
        request_id=request_id,
        answer=result.answer,
        model=result.model,
        provider=result.provider,
        steps=result.steps,
        status=result.status,
        latency_ms=latency_ms,
        tool_calls=result.tool_calls,
        sources=result.sources,
        trace=result.trace,
    )
