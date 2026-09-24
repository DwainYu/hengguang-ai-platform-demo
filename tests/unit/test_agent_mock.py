"""Unit tests for MockProvider deterministic tool calling (Day 3)."""

from __future__ import annotations

import pytest

from app.gateway.base import ModelResponse
from app.gateway.mock import CONTEXT_HEADER, NO_CONTEXT_BODY, MockProvider


def _schema(name: str) -> dict:
    """Minimal OpenAI function schema; the mock only reads function.name."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"{name} test",
            "parameters": {"type": "object", "properties": {}},
        },
    }


KNOWLEDGE_TOOLS = [_schema("knowledge_search"), _schema("document_lookup")]

CONTEXT_BLOCK = (
    f"{CONTEXT_HEADER}\n[1] 测试文档 · 主营业务\n恒光主要从事无机精细化学品的研发、生产和销售。"
)


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider()


async def call(
    provider: MockProvider, message: str, tools: list[dict] | None = None
) -> ModelResponse:
    return await provider.chat(
        [{"role": "user", "content": message}], model="mock-model", tools=tools
    )


class TestMockToolCalling:
    """Deterministic tool-call decisions (SPEC section 16)."""

    async def test_knowledge_query_becomes_knowledge_search_call(self, provider: MockProvider):
        response = await call(provider, "恒光主要有哪些业务？", KNOWLEDGE_TOOLS)
        assert response.tool_calls, "expected a tool call"
        assert response.content == ""
        call_obj = response.tool_calls[0]
        assert call_obj.name == "knowledge_search"
        assert call_obj.arguments == {"query": "恒光主要有哪些业务？"}
        assert call_obj.id.startswith("call_knowledge_search_")

    async def test_tool_call_is_deterministic(self, provider: MockProvider):
        first = await call(provider, "恒光主要有哪些业务？", KNOWLEDGE_TOOLS)
        second = await call(MockProvider(), "恒光主要有哪些业务？", KNOWLEDGE_TOOLS)
        assert first.tool_calls[0].name == second.tool_calls[0].name
        assert first.tool_calls[0].arguments == second.tool_calls[0].arguments

    async def test_greeting_gets_final_answer_without_tools(self, provider: MockProvider):
        response = await call(provider, "你好", KNOWLEDGE_TOOLS)
        assert response.tool_calls == []
        assert "你好" in response.content

    async def test_creative_request_gets_explicit_no_information_answer(
        self, provider: MockProvider
    ):
        response = await call(provider, "帮我写一首诗", KNOWLEDGE_TOOLS)
        assert response.tool_calls == []
        assert "没有足够信息" in response.content

    async def test_document_lookup_becomes_document_lookup_call(self, provider: MockProvider):
        response = await call(provider, "查看某份公开资料的详细信息", KNOWLEDGE_TOOLS)
        assert response.tool_calls
        call_obj = response.tool_calls[0]
        assert call_obj.name == "document_lookup"
        assert call_obj.arguments == {"document_id": "hengguang-public-profile"}

    async def test_document_lookup_uses_keyword_hints(self, provider: MockProvider):
        response = await call(provider, "查看2025年年报的详细信息", KNOWLEDGE_TOOLS)
        assert response.tool_calls[0].arguments == {"document_id": "hengguang-annual-report-2025"}

    async def test_scripted_provider_replays_tool_calls(self):
        provider = MockProvider(script=["knowledge_search", "document_lookup"])
        first = await call(provider, "随便什么消息", KNOWLEDGE_TOOLS)
        second = await call(provider, "随便什么消息", KNOWLEDGE_TOOLS)
        assert [c.name for c in first.tool_calls] == ["knowledge_search"]
        assert [c.name for c in second.tool_calls] == ["document_lookup"]

    async def test_scripted_provider_exhausts_into_final_answer(self):
        provider = MockProvider(script=["knowledge_search"])
        await call(provider, "随便什么消息", KNOWLEDGE_TOOLS)
        response = await call(provider, "随便什么消息", KNOWLEDGE_TOOLS)
        assert response.tool_calls == []
        assert response.content

    async def test_final_answer_built_from_tool_result_keeps_citations(
        self, provider: MockProvider
    ):
        messages = [
            {"role": "user", "content": "恒光主要有哪些业务？"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_knowledge_search_1",
                        "type": "function",
                        "function": {"name": "knowledge_search", "arguments": '{"query": "x"}'},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call_knowledge_search_1", "content": CONTEXT_BLOCK},
        ]
        response = await provider.chat(messages, model="mock-model", tools=KNOWLEDGE_TOOLS)
        assert response.tool_calls == []
        assert "无机精细化学品" in response.content
        assert "[1]" in response.content

    async def test_empty_tool_result_reports_no_information(self, provider: MockProvider):
        messages = [
            {"role": "user", "content": "恒光主要有哪些业务？"},
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": f"{CONTEXT_HEADER}\n{NO_CONTEXT_BODY}",
            },
        ]
        response = await provider.chat(messages, model="mock-model", tools=KNOWLEDGE_TOOLS)
        assert response.tool_calls == []
        assert "没有足够信息" in response.content

    async def test_plain_mode_unchanged_without_tools(self, provider: MockProvider):
        """Day-1 behaviour: no tools -> canned response, no tool calls."""
        response = await call(provider, "测试消息")
        assert response.tool_calls == []
        assert response.content == "[Mock] 收到您的消息：测试消息"
