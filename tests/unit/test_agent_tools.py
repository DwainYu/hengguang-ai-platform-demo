"""Unit tests for the Day-3 tool layer: registry, schema, executor."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field, ValidationError

from app.agent.executor import ToolExecutor
from app.agent.registry import ToolRegistry
from app.agent.tools.base import Tool, ToolResult
from app.gateway.base import ToolCall


class EchoArgs(BaseModel):
    text: str = Field(..., min_length=1)
    times: int = Field(default=2, ge=1, le=3)


class EchoTool(Tool):
    """Test double: repeats text N times, explodes on demand."""

    name = "echo"
    description = "Return the text repeated N times."
    args_model = EchoArgs

    async def execute(self, arguments: dict) -> ToolResult:
        if arguments["text"] == "boom":
            raise RuntimeError("boom")
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=arguments["text"] * arguments["times"],
            metadata={"times": arguments["times"]},
        )


@pytest.fixture
def registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(EchoTool())
    return registry


class TestToolRegistry:
    """Registry: register / duplicate / get / unknown / list."""

    def test_register_and_get(self, registry: ToolRegistry):
        tool = registry.get("echo")
        assert isinstance(tool, EchoTool)

    def test_duplicate_registration_fails(self, registry: ToolRegistry):
        with pytest.raises(ValueError, match="already registered"):
            registry.register(EchoTool())

    def test_unknown_tool_fails(self, registry: ToolRegistry):
        with pytest.raises(KeyError, match="Unknown tool"):
            registry.get("missing")

    def test_list_returns_registered_tools(self, registry: ToolRegistry):
        assert registry.names() == ["echo"]
        assert [type(tool) for tool in registry.list()] == [EchoTool]

    def test_openai_schemas_shape(self, registry: ToolRegistry):
        schemas = registry.openai_schemas()
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "echo"
        assert schema["function"]["description"]
        assert schema["function"]["parameters"]["type"] == "object"


class TestToolSchema:
    """Tool parameters must be the single source of truth for the LLM schema."""

    def test_schema_is_generated_from_args_model(self, registry: ToolRegistry):
        parameters = registry.get("echo").parameters
        assert set(parameters["properties"]) == {"text", "times"}
        assert parameters["required"] == ["text"]

    def test_default_value_in_schema(self, registry: ToolRegistry):
        assert registry.get("echo").parameters["properties"]["times"]["default"] == 2

    def test_bounds_in_schema(self, registry: ToolRegistry):
        times = registry.get("echo").parameters["properties"]["times"]
        assert times["minimum"] == 1
        assert times["maximum"] == 3

    def test_validate_fills_defaults(self, registry: ToolRegistry):
        assert registry.get("echo").validate({"text": "x"}) == {"text": "x", "times": 2}

    def test_validate_rejects_missing_required(self, registry: ToolRegistry):
        with pytest.raises(ValidationError):
            registry.get("echo").validate({"times": 1})

    def test_validate_rejects_wrong_type(self, registry: ToolRegistry):
        with pytest.raises(ValidationError):
            registry.get("echo").validate({"text": "x", "times": "many"})

    def test_validate_rejects_out_of_range(self, registry: ToolRegistry):
        with pytest.raises(ValidationError):
            registry.get("echo").validate({"text": "x", "times": 99})


class TestToolExecutor:
    """Executor: success / unknown tool / malformed arguments / tool exception."""

    async def test_successful_execution(self, registry: ToolRegistry):
        executor = ToolExecutor(registry)
        result = await executor.execute(
            ToolCall(id="call_1", name="echo", arguments={"text": "ab", "times": 3})
        )
        assert result.success is True
        assert result.content == "ababab"
        assert result.error is None
        assert result.metadata == {"times": 3}

    async def test_successful_execution_uses_default_arguments(self, registry: ToolRegistry):
        executor = ToolExecutor(registry)
        result = await executor.execute(ToolCall(id="call_1", name="echo", arguments={"text": "x"}))
        assert result.success is True
        assert result.content == "xx"

    async def test_unknown_tool_becomes_failure(self, registry: ToolRegistry):
        executor = ToolExecutor(registry)
        result = await executor.execute(ToolCall(id="call_2", name="missing", arguments={}))
        assert result.success is False
        assert "Unknown tool" in (result.error or "")
        assert result.content == ""

    async def test_malformed_arguments_become_failure(self, registry: ToolRegistry):
        executor = ToolExecutor(registry)
        result = await executor.execute(ToolCall(id="call_3", name="echo", arguments={"times": 1}))
        assert result.success is False
        assert "Invalid arguments" in (result.error or "")
        assert "text" in (result.error or "")

    async def test_tool_exception_becomes_failure(self, registry: ToolRegistry):
        executor = ToolExecutor(registry)
        result = await executor.execute(
            ToolCall(id="call_4", name="echo", arguments={"text": "boom"})
        )
        assert result.success is False
        assert "RuntimeError" in (result.error or "")
        assert "boom" in (result.error or "")
