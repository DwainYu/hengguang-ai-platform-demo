"""Tool executor: validate -> registry lookup -> execute -> ToolResult (Day 3).

Knows nothing about individual business tools: it only calls the generic
``Tool`` interface, so every failure mode (unknown tool, malformed arguments,
tool exception) becomes a controlled ``ToolResult`` failure.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.agent.registry import ToolRegistry
from app.agent.tools.base import ToolResult
from app.gateway.base import ToolCall


def _validation_summary(error: ValidationError) -> str:
    """Compact one-line summary of a pydantic ValidationError."""
    parts = []
    for item in error.errors():
        loc = ".".join(str(part) for part in item.get("loc", []))
        parts.append(f"{loc}: {item.get('msg')}" if loc else str(item.get("msg")))
    return "; ".join(parts)


class ToolExecutor:
    """Runs tool calls on behalf of the agent loop."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    async def execute(self, call: ToolCall) -> ToolResult:
        """Execute one tool call; never raises — failures become ToolResults."""
        try:
            tool = self._registry.get(call.name)
        except KeyError:
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                error=f"Unknown tool: {call.name}",
            )

        try:
            arguments = tool.validate(call.arguments)
        except ValidationError as error:
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                error=f"Invalid arguments for '{call.name}': {_validation_summary(error)}",
            )

        try:
            return await tool.execute(arguments)
        except Exception as error:  # noqa: BLE001 — the boundary that contains tools
            return ToolResult(
                tool_name=call.name,
                success=False,
                content="",
                error=f"Tool '{call.name}' failed: {type(error).__name__}: {error}",
            )
