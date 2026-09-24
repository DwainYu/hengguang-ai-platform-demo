"""Agent schemas: state, trace step, run result (Day 3).

Everything one agent run needs lives in :class:`AgentState` — not scattered
across services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agent.tools.base import ToolResult
from app.gateway.base import ToolCall


@dataclass
class TraceStep:
    """One execution-trace entry (minimal observability, Day 4 expands it)."""

    step: int
    type: str  # "llm" | "tool_call" | "final" | "stopped"
    tool: str | None = None
    latency_ms: int = 0
    detail: str | None = None


@dataclass
class AgentState:
    """Mutable state of a single agent run."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    step: int = 0
    model: str = ""
    provider: str = ""
    final_answer: str | None = None
    trace: list[TraceStep] = field(default_factory=list)


@dataclass
class AgentRunResult:
    """Outcome of one ``AgentRuntime.run`` call."""

    answer: str
    model: str
    provider: str
    steps: int
    status: str  # "completed" | "max_steps" | "max_tool_calls"
    tool_calls: list[dict] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
