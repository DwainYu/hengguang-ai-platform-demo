"""Tool registry: whitelisted tools, unique names, clear errors (Day 3)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # type-only: avoids the tools/__init__ <-> registry import cycle
    from app.agent.tools.base import Tool


class ToolRegistry:
    """Registry that maps tool names to tools, decoupled from implementations.

    * tool names are unique — duplicate registration fails explicitly;
    * unknown tools fail explicitly (KeyError) instead of returning None;
    * business code depends on this registry, never on concrete tools.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool; raises ValueError on duplicate names."""
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Look up a tool by name; raises KeyError for unknown tools."""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool: {name}")
        return tool

    def list(self) -> list[Tool]:
        """All registered tools, in registration order."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """All registered tool names, in registration order."""
        return list(self._tools)

    def openai_schemas(self) -> list[dict]:
        """OpenAI function schemas for every registered tool."""
        return [tool.to_openai_schema() for tool in self._tools.values()]
