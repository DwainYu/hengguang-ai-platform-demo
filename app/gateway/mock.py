"""MockProvider: deterministic canned responses so tests run without API keys."""

from __future__ import annotations

import time

from app.gateway.base import BaseProvider, ModelResponse


class MockProvider(BaseProvider):
    """Deterministic mock provider for testing and offline development.

    Returns canned responses based on the last user message content.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def _chat_impl(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        temperature: float,
        response_format: dict | None,
    ) -> ModelResponse:
        start = time.perf_counter()

        # Get the last user message
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break

        # Deterministic canned responses for demo scenarios
        if "恒光" in user_msg and "业务" in user_msg:
            content = (
                "根据公开资料，湖南恒光科技股份有限公司主要从事无机精细化学品的研发、生产和销售，"
                "核心产品包括氯碱系列产品（如盐酸、液碱、次氯酸钠等）以及相关化工新材料。"
                "公司在化工行业有一定的市场地位，持续进行技术创新和产能优化。"
            )
        elif "采购" in user_msg and "价格" in user_msg:
            content = (
                "基于合成 ERP 数据分析，最近 30 天主要原材料采购价格呈现小幅波动："
                "盐酸均价约 320 元/吨（+2.1%），液碱均价约 1850 元/吨（-1.3%），"
                "次氯酸钠均价约 680 元/吨（+0.8%）。整体趋势相对平稳。"
            )
        elif "安全" in user_msg and ("区域" in user_msg or "车间" in user_msg):
            content = (
                "根据合成安全事件数据，最近一个月 A 车间记录 12 起安全事件（占比 40%），"
                "B 车间 7 起，C 车间 5 起。A 车间主要为操作规程违规和设备隐患，"
                "建议重点加强岗前培训和设备巡检。"
            )
        elif "你好" in user_msg or "hello" in user_msg.lower():
            content = "你好！我是恒光 AI 平台的模拟助手。有什么可以帮您的吗？"
        else:
            content = f"[Mock] 收到您的消息：{user_msg[:100]}"

        latency_ms = int((time.perf_counter() - start) * 1000)

        return ModelResponse(
            content=content,
            model=model or "mock-model",
            provider=self.provider_name,
            usage={"prompt_tokens": len(user_msg), "completion_tokens": len(content)},
            latency_ms=latency_ms,
        )
