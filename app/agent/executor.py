"""Tool executor: registry lookup → permission check → validate → execute.

Day 3 made every failure a controlled ``ToolResult``. Day 4 adds the *authority*
boundary in the same place, so RBAC also holds inside the agent loop: the role of
the caller is checked against ``Tool.permission`` **before** any business code or
SQL runs, and a denial is returned as a structured ``PERMISSION_DENIED`` failure
instead of raising — the agent can then still produce a controlled final answer.

Each executed (or denied) call also becomes one compact audit row plus a metrics
counter, tagged with the request id of the run.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import ValidationError

from app.agent.registry import ToolRegistry
from app.agent.tools.base import Tool, ToolResult
from app.api.errors import ERROR_PERMISSION_DENIED
from app.auth.permissions import has_permission
from app.gateway.base import ToolCall
from app.observability.audit import Actor, AuditLog, AuditStatus
from app.observability.metrics import Metrics
from app.observability.metrics import metrics as default_metrics

logger = logging.getLogger("app.agent.executor")

ERROR_UNKNOWN_TOOL = "UNKNOWN_TOOL"
ERROR_TOOL_FAILED = "TOOL_ERROR"
ERROR_INVALID_ARGUMENTS = "INVALID_ARGUMENTS"


def _validation_summary(error: ValidationError) -> str:
    """Compact one-line summary of a pydantic ValidationError."""
    parts = []
    for item in error.errors():
        loc = ".".join(str(part) for part in item.get("loc", []))
        parts.append(f"{loc}: {item.get('msg')}" if loc else str(item.get("msg")))
    return "; ".join(parts)


AUDITABLE_ARGUMENT_KEYS = ("operation", "days", "limit", "material", "area", "status", "mode")


def _audit_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    """Params we may store: operation/days/limit only — never prompt or result text."""

    summary: dict[str, Any] = {}
    for key in AUDITABLE_ARGUMENT_KEYS:
        value = arguments.get(key)
        if isinstance(value, (int, float, bool)) or isinstance(value, str):
            summary[key] = value if not isinstance(value, str) else value[:80]
    return summary


class ToolExecutor:
    """Runs tool calls on behalf of the agent loop, enforcing tool permissions."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        audit: AuditLog | None = None,
        metrics: Metrics | None = None,
    ) -> None:
        self._registry = registry
        self._audit = audit
        self._metrics = metrics if metrics is not None else default_metrics

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    def permission_for(self, tool_name: str) -> str | None:
        """Permission required by a registered tool (``None`` for unknown tools)."""

        try:
            tool: Tool = self._registry.get(tool_name)
        except KeyError:
            return None
        return str(tool.permission)

    def is_allowed(self, tool_name: str, actor: Actor | None) -> bool:
        """True when ``actor`` may execute ``tool_name`` (no actor → no RBAC layer)."""

        if actor is None or not actor.is_authenticated:
            return True
        try:
            tool = self._registry.get(tool_name)
        except KeyError:
            return False
        return has_permission(actor.role, tool.permission)

    async def execute(self, call: ToolCall, *, actor: Actor | None = None) -> ToolResult:
        """Execute one tool call; never raises — failures become ToolResults."""

        started = time.perf_counter()
        result = await self._execute(call, actor)
        self._observe(call, result, actor, started)
        return result

    async def _execute(self, call: ToolCall, actor: Actor | None) -> ToolResult:
        try:
            tool = self._registry.get(call.name)
        except KeyError:
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                error=f"Unknown tool: {call.name}",
                error_code=ERROR_UNKNOWN_TOOL,
            )

        # ---- RBAC at the agent layer: checked before the tool touches any data.
        if actor is None or not actor.is_authenticated:
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                metadata={"permission_required": str(tool.permission)},
                error=(
                    f"权限不足（{ERROR_PERMISSION_DENIED}）：未认证请求不允许使用工具 '{call.name}'"
                ),
                error_code=ERROR_PERMISSION_DENIED,
            )
        if not has_permission(actor.role, tool.permission):
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                metadata={"permission_required": str(tool.permission), "role": actor.role},
                error=(
                    f"权限不足（{ERROR_PERMISSION_DENIED}）：角色 '{actor.role}' 不允许使用工具 "
                    f"'{call.name}'（需要权限 '{tool.permission}'）"
                ),
                error_code=ERROR_PERMISSION_DENIED,
            )

        try:
            arguments = tool.validate(call.arguments)
        except ValidationError as error:
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                error=f"Invalid arguments for '{call.name}': {_validation_summary(error)}",
                error_code=ERROR_INVALID_ARGUMENTS,
            )

        try:
            return await tool.execute(arguments)
        except Exception as error:  # noqa: BLE001 — the boundary that contains tools
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                error=f"Tool '{call.name}' failed: {type(error).__name__}: {error}",
                error_code=ERROR_TOOL_FAILED,
            )

    def _observe(
        self, call: ToolCall, result: ToolResult, actor: Actor | None, started: float
    ) -> None:
        """Metrics + audit for one executed/denied call (best effort, never raises)."""

        permission_denied = result.error_code == ERROR_PERMISSION_DENIED
        self._metrics.observe_tool_call(
            tool=call.name,
            success=result.success,
            permission_denied=permission_denied,
        )
        if actor is None or not actor.is_authenticated or self._audit is None:
            return
        latency_ms = int((time.perf_counter() - started) * 1000)
        if result.success:
            status = AuditStatus.SUCCESS
        elif permission_denied:
            status = AuditStatus.DENIED
        else:
            status = AuditStatus.ERROR
        logger.info(
            "tool call",
            extra={
                "event": "tool.call",
                "request_id": actor.request_id,
                "user_id": actor.user_id,
                "role": actor.role,
                "tool": call.name,
                "operation": result.metadata.get("operation") or "",
                "status": str(status),
                "result_count": result.metadata.get("result_count", 0),
                "latency_ms": latency_ms,
                "error_code": result.error_code or "",
            },
        )
        self._audit.record_tool_call(
            actor,
            tool_name=call.name,
            status=status,
            model_name=actor.extra.get("model"),
            input_summary={
                **_audit_summary(call.arguments),
                "error_code": result.error_code or "",
            },
            latency_ms=latency_ms,
        )


__all__ = [
    "ERROR_INVALID_ARGUMENTS",
    "ERROR_TOOL_FAILED",
    "ERROR_UNKNOWN_TOOL",
    "ToolExecutor",
]
