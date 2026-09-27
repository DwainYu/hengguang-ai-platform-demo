"""Unit tests for the AgentRuntime loop and safety limits (Day 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agent.registry import ToolRegistry
from app.agent.runtime import (
    STATUS_COMPLETED,
    STATUS_MAX_STEPS,
    STATUS_MAX_TOOL_CALLS,
    AgentRuntime,
)
from app.agent.tools.base import Tool, ToolResult
from app.auth.auth import DEMO_ADMIN
from app.config import Settings
from app.gateway.mock import MockProvider
from app.gateway.router import ModelGateway
from app.observability.audit import Actor


class SearchArgs(BaseModel):
    query: str = Field(..., min_length=1)


class LookupArgs(BaseModel):
    document_id: str = Field(..., min_length=1)


class StrictLookupArgs(BaseModel):
    """Requires an argument the mock never sends (drives validation failures)."""

    document_id: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)


class StubSearchTool(Tool):
    name = "knowledge_search"
    description = "stub knowledge tool"
    args_model = SearchArgs

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=f"stub result: {arguments['query']}",
            metadata={
                "result_count": 1,
                "sources": [
                    {
                        "document_id": "doc-1",
                        "title": "Doc 1",
                        "source": "public",
                        "citation": "[1]",
                    }
                ],
            },
        )


class StubLookupTool(Tool):
    name = "document_lookup"
    description = "stub lookup tool"
    args_model = LookupArgs

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=f"stub document: {arguments['document_id']}",
            metadata={"document_id": arguments["document_id"]},
        )


class ExplodingSearchTool(StubSearchTool):
    """Simulates the knowledge base being unavailable."""

    async def execute(self, arguments: dict) -> ToolResult:
        raise RuntimeError("Chroma unavailable")


def make_registry(*tools: Tool) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry


def make_runtime(
    *,
    script: list[str] | None = None,
    max_steps: int = 5,
    max_tool_calls: int = 8,
    registry: ToolRegistry | None = None,
) -> AgentRuntime:
    gateway = ModelGateway(providers={"mock": MockProvider(script=script)})
    return AgentRuntime(
        gateway,
        registry or make_registry(StubSearchTool(), StubLookupTool()),
        config=Settings(agent_max_steps=max_steps, agent_max_tool_calls=max_tool_calls),
    )


class TestAgentRuntime:
    """Runtime: final answer / tool calls / loop limits / failures."""

    async def test_direct_final_answer_without_tools(self):
        runtime = make_runtime()
        result = await runtime.run("你好")
        assert result.status == STATUS_COMPLETED
        assert result.steps == 1
        assert result.tool_calls == []
        assert result.sources == []
        assert result.answer
        assert result.model == "mock-model"
        assert result.provider == "mock"
        assert result.trace[-1]["type"] == "final"

    async def test_one_tool_call_then_final(self):
        runtime = make_runtime()
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_COMPLETED
        assert result.steps == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "knowledge_search"
        assert result.tool_calls[0]["arguments"] == {"query": "恒光主要有哪些业务？"}
        assert result.tool_calls[0]["success"] is True
        # sources survive from the tool metadata into the run result
        assert result.sources == [
            {"document_id": "doc-1", "title": "Doc 1", "source": "public", "citation": "[1]"}
        ]
        assert "stub result" in result.answer
        trace_types = [entry["type"] for entry in result.trace]
        assert trace_types == ["llm", "tool_call", "llm", "final"]

    async def test_multiple_tool_calls(self):
        runtime = make_runtime(script=["knowledge_search", "document_lookup"])
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_COMPLETED
        assert result.steps == 3
        assert [call["name"] for call in result.tool_calls] == [
            "knowledge_search",
            "document_lookup",
        ]
        assert "stub document" in result.answer

    async def test_max_steps_stops_the_loop(self):
        runtime = make_runtime(script=["knowledge_search"] * 20, max_steps=3)
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_MAX_STEPS
        assert result.steps == 3
        assert len(result.tool_calls) == 3
        assert "安全限制" in result.answer
        assert result.trace[-1]["type"] == "stopped"
        assert all(entry["type"] != "final" for entry in result.trace)

    async def test_max_tool_calls_stops_the_loop(self):
        runtime = make_runtime(script=["knowledge_search"] * 20, max_steps=10, max_tool_calls=2)
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_MAX_TOOL_CALLS
        assert result.steps == 2
        assert len(result.tool_calls) == 2
        assert "安全限制" in result.answer

    async def test_unknown_tool_is_not_executed_but_loop_terminates(self):
        runtime = make_runtime(script=["nonexistent_tool"])
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_COMPLETED
        assert result.steps == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["success"] is False
        assert "Unknown tool" in (result.tool_calls[0]["error"] or "")
        assert "Unknown tool" in result.answer

    async def test_tool_failure_is_returned_as_controlled_result(self):
        runtime = make_runtime(registry=make_registry(ExplodingSearchTool(), StubLookupTool()))
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_COMPLETED
        assert result.steps == 2
        assert result.tool_calls[0]["success"] is False
        assert "Chroma unavailable" in (result.tool_calls[0]["error"] or "")
        assert "工具执行失败" in result.answer
        assert result.sources == []

    async def test_malformed_tool_arguments_are_not_executed(self):
        class StrictLookupTool(StubLookupTool):
            args_model = StrictLookupArgs

        runtime = make_runtime(
            registry=make_registry(StubSearchTool(), StrictLookupTool()),
            script=["document_lookup"],
            max_steps=1,
        )
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["success"] is False
        assert "Invalid arguments" in (result.tool_calls[0]["error"] or "")
        assert result.steps == 1

    async def test_empty_tool_result_reports_no_information(self):
        class EmptySearchTool(StubSearchTool):
            async def execute(self, arguments: dict) -> ToolResult:
                return ToolResult(tool_name=self.name, success=True, content="", metadata={})

        runtime = make_runtime(registry=make_registry(EmptySearchTool()))
        result = await runtime.run(
            "恒光主要有哪些业务？", actor=Actor.from_user(DEMO_ADMIN, "req_test")
        )
        assert result.status == STATUS_COMPLETED
        assert result.steps == 2
        assert "没有足够信息" in result.answer
