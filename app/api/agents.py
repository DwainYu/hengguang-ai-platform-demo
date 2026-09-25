"""POST /api/agent/run — Agent Runtime entry point (Day 3) behind RBAC + audit (Day 4).

The route only checks ``agent:run``; **tool-level** permissions are enforced deeper
in the loop by the :class:`~app.agent.executor.ToolExecutor`. So an operator asking
about ERP purchase data gets a 200 response whose ``tool_calls`` entry is a
controlled ``PERMISSION_DENIED`` failure and whose ``answer`` is still usable —
exactly the behaviour Day 4 requires for the agent layer.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.api.errors import ERROR_INTERNAL, PlatformError
from app.auth.auth import CurrentUser
from app.auth.dependencies import require
from app.auth.permissions import Permission
from app.observability.audit import Actor, AuditAction, AuditLog, AuditStatus, get_audit_log
from app.observability.logging import get_logger
from app.observability.middleware import request_id_of
from app.services.agent_service import AgentService, get_agent_service

router = APIRouter(prefix="/api/agent", tags=["agent"])

MAX_REQUEST_STEPS = 20

AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
RequestIdDep = Annotated[str, Depends(request_id_of)]
AuditLogDep = Annotated[AuditLog, Depends(get_audit_log)]
AgentUserDep = Annotated[CurrentUser, Depends(require(Permission.AGENT_RUN))]

logger = get_logger("app.api.agents")


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
    """One executed tool call, with its outcome (Day-4 error codes included)."""

    name: str
    arguments: dict = {}
    success: bool | None = None
    error: str | None = None
    error_code: str | None = None
    operation: str | None = None
    result_count: int | None = None


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
    user: str = ""
    role: str = ""
    tool_calls: list[AgentToolCallOut] = []
    sources: list[AgentSourceOut] = []
    trace: list[AgentTraceOut] = []


@router.post("/run", response_model=AgentRunResponse)
async def agent_run(
    payload: AgentRunRequest,
    service: AgentServiceDep,
    request_id: RequestIdDep,
    user: AgentUserDep,
    audit: AuditLogDep,
) -> AgentRunResponse:
    """Run the agent loop: model -> permission-checked tools -> final answer."""

    actor = Actor.from_user(user, request_id)
    started = time.perf_counter()
    try:
        result = await service.run(payload.message, actor=actor, max_steps=payload.max_steps)
    except PlatformError:
        raise
    except Exception as error:  # the runtime contains tool/provider errors; this is the last net
        latency_ms = int((time.perf_counter() - started) * 1000)
        audit.record_api(
            actor,
            action=AuditAction.AGENT_RUN,
            status=AuditStatus.ERROR,
            endpoint="POST /api/agent/run",
            mode="agent",
            input_summary={"chars": len(payload.message), "error_code": ERROR_INTERNAL},
            latency_ms=latency_ms,
        )
        logger.exception(
            "agent run failed",
            extra={"event": "agent.run_error", "error_type": type(error).__name__},
        )
        raise PlatformError(
            "Agent 运行失败，请使用 request_id 查询审计日志。",
            code=ERROR_INTERNAL,
            status_code=500,
            details={"error_type": type(error).__name__},
        ) from error

    latency_ms = int((time.perf_counter() - started) * 1000)
    denied = [call for call in result.tool_calls if call.get("error_code") == "PERMISSION_DENIED"]
    audit.record_api(
        actor,
        action=AuditAction.AGENT_RUN,
        status=AuditStatus.DENIED
        if denied and not _any_success(result.tool_calls)
        else AuditStatus.SUCCESS,
        endpoint="POST /api/agent/run",
        request_id=request_id,
        model_name=result.model,
        mode="agent",
        input_summary={
            "chars": len(payload.message),
            "steps": result.steps,
            "tool_calls": len(result.tool_calls),
            "denied_calls": len(denied),
            "run_status": result.status,
        },
        latency_ms=latency_ms,
    )
    return AgentRunResponse(
        request_id=result.request_id or request_id,
        answer=result.answer,
        model=result.model,
        provider=result.provider,
        steps=result.steps,
        status=result.status,
        latency_ms=latency_ms,
        user=user.username,
        role=user.role,
        tool_calls=result.tool_calls,
        sources=result.sources,
        trace=result.trace,
    )


def _any_success(tool_calls: list[dict]) -> bool:
    return any(call.get("success") for call in tool_calls)
