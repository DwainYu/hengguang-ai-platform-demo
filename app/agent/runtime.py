"""AgentRuntime: the agent loop (Day 3).

    user message -> ModelGateway -> tool call? -> ToolExecutor -> ToolResult
                 ^                                                     |
                 +-----------------------------------------------------+
                 (until final answer, max_steps or max_tool_calls)

All model access goes through ``ModelGateway`` (SPEC section 0.1 rule 3); all
tool access goes through the whitelisted ``ToolRegistry`` (rule 4).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any

from app.agent.executor import ToolExecutor
from app.agent.models import AgentRunResult, AgentState, TraceStep
from app.agent.prompts import build_agent_messages
from app.agent.registry import ToolRegistry
from app.agent.tools.base import ToolResult
from app.config import Settings, settings
from app.gateway.base import ModelResponse, ToolCall
from app.gateway.router import ModelGateway

STATUS_COMPLETED = "completed"
STATUS_MAX_STEPS = "max_steps"
STATUS_MAX_TOOL_CALLS = "max_tool_calls"


def _assistant_message(response: ModelResponse) -> dict[str, Any]:
    """OpenAI-compatible assistant message, carrying requested tool calls."""
    message: dict[str, Any] = {"role": "assistant", "content": response.content or ""}
    if response.tool_calls:
        message["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments, ensure_ascii=False),
                },
            }
            for call in response.tool_calls
        ]
    return message


def _tool_message(call: ToolCall, result: ToolResult) -> dict[str, Any]:
    """OpenAI-compatible tool-result message; failures stay readable for the model."""
    content = result.content if result.success else f"工具执行失败：{result.error}"
    return {"role": "tool", "tool_call_id": call.id, "content": content}


def _result_detail(result: ToolResult) -> str:
    """Human-readable one-liner for the trace, e.g. `3 chunks`."""
    if not result.success:
        return result.error or "failed"
    count = result.metadata.get("result_count")
    if isinstance(count, int):
        return f"{count} chunks"
    return "ok"


class AgentRuntime:
    """Runs the tool-calling loop with hard safety limits.

    * ``max_steps`` bounds the number of LLM rounds;
    * ``max_tool_calls`` bounds the number of executed tool calls;
    * unknown tools and malformed arguments are never executed;
    * tool exceptions become ToolResult failures returned to the model;
    * the loop always terminates.
    """

    def __init__(
        self,
        gateway: ModelGateway,
        registry: ToolRegistry,
        *,
        config: Settings | None = None,
    ) -> None:
        self._gateway = gateway
        self._registry = registry
        self._executor = ToolExecutor(registry)
        cfg = config or settings
        self._max_steps = cfg.agent_max_steps
        self._max_tool_calls = cfg.agent_max_tool_calls

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    async def run(
        self,
        message: str,
        *,
        max_steps: int | None = None,
        max_tool_calls: int | None = None,
    ) -> AgentRunResult:
        """Run the agent loop for one user message."""
        step_budget = max_steps or self._max_steps
        tool_budget = max_tool_calls or self._max_tool_calls

        state = AgentState(messages=build_agent_messages(message))
        tools = self._registry.openai_schemas()
        stop_reason: str | None = None

        while True:
            if state.step >= step_budget:
                stop_reason = STATUS_MAX_STEPS
                break
            if len(state.tool_results) >= tool_budget:
                stop_reason = STATUS_MAX_TOOL_CALLS
                break

            state.step += 1
            response = await self._gateway.chat(state.messages, tools=tools)
            state.model, state.provider = response.model, response.provider
            state.messages.append(_assistant_message(response))
            state.trace.append(
                TraceStep(
                    step=state.step,
                    type="llm",
                    tool=response.tool_calls[0].name if response.tool_calls else None,
                    latency_ms=response.latency_ms,
                )
            )

            if not response.tool_calls:
                state.final_answer = response.content
                state.trace.append(TraceStep(step=state.step, type="final"))
                break

            for call in response.tool_calls:
                if len(state.tool_results) >= tool_budget:
                    # While-loop top check turns this into a max_tool_calls stop.
                    break
                started = time.perf_counter()
                result = await self._executor.execute(call)
                state.tool_calls.append(call)
                state.tool_results.append(result)
                state.messages.append(_tool_message(call, result))
                state.sources.extend(result.metadata.get("sources", []))
                state.trace.append(
                    TraceStep(
                        step=state.step,
                        type="tool_call",
                        tool=call.name,
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        detail=_result_detail(result),
                    )
                )

        if state.final_answer is None:  # safety stop: no final answer was generated
            state.final_answer = (
                f"Agent 已在安全限制处停止（{stop_reason}）："
                f"共执行 {len(state.tool_results)} 次工具调用、{state.step} 步，未生成最终回答。"
            )
            state.trace.append(
                TraceStep(
                    step=state.step,
                    type="stopped",
                    detail=stop_reason,
                )
            )

        tool_call_payloads = [
            {
                "name": call.name,
                "arguments": call.arguments,
                "success": result.success,
                "error": result.error,
            }
            for call, result in zip(state.tool_calls, state.tool_results, strict=True)
        ]
        return AgentRunResult(
            answer=state.final_answer,
            model=state.model,
            provider=state.provider,
            steps=state.step,
            status=stop_reason or STATUS_COMPLETED,
            tool_calls=tool_call_payloads,
            sources=state.sources,
            trace=[asdict(entry) for entry in state.trace],
        )
