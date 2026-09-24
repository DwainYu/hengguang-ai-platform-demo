"""MockProvider: deterministic canned responses so tests run without API keys."""

from __future__ import annotations

import re
import time

from app.gateway.base import BaseProvider, ModelResponse
from app.rag.prompt import CONTEXT_HEADER, NO_CONTEXT_BODY

_CITATION_LINE_RE = re.compile(r"^\[(\d+)\]\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；])")
_MAX_CITED_SOURCES = 3
_MAX_SENTENCE_CHARS = 120


def _find_rag_context(messages: list[dict[str, str]]) -> str | None:
    """Return the retrieved-context block if the prompt carries one."""
    for msg in messages:
        content = msg.get("content", "") or ""
        if content.startswith(CONTEXT_HEADER):
            return content
    return None


def _parse_context(block: str) -> list[tuple[int, str, str]]:
    """Split the context block into (index, citation label, chunk text)."""
    entries: list[tuple[int, str, str]] = []
    current: tuple[int, str] | None = None
    body: list[str] = []
    for line in block.splitlines()[1:]:
        match = _CITATION_LINE_RE.match(line.strip())
        if match:
            if current is not None:
                entries.append((current[0], current[1], "\n".join(body).strip()))
            current = (int(match.group(1)), match.group(2).strip())
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        entries.append((current[0], current[1], "\n".join(body).strip()))
    return entries


def _candidate_sentences(text: str) -> list[str]:
    """Readable statements: no headings, no blockquote disclaimers, no table rules."""
    lines = [line.strip() for line in text.splitlines()]
    separator = re.compile(r"[|:\-\s]+")
    candidates: list[str] = []
    for position, line in enumerate(lines):
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        if separator.fullmatch(line):  # markdown table separator row
            continue
        following_is_separator = position + 1 < len(lines) and bool(
            separator.fullmatch(lines[position + 1])
        )
        if following_is_separator:  # table header row, the data rows carry the facts
            continue
        line = line.replace("**", "")
        if line.startswith("|") and line.endswith("|"):
            line = " / ".join(cell.strip() for cell in line.strip("|").split("|") if cell.strip())
        for part in _SENTENCE_SPLIT_RE.split(line):
            part = part.strip().lstrip("-* ").strip().rstrip("，、")
            if len(part) >= 10:
                candidates.append(part)
    return candidates


def _best_sentences(text: str, question: str, limit: int = 2) -> str:
    """Pick the statements that share the most 2-grams with the question."""
    grams = {question[i : i + 2] for i in range(len(question) - 1) if question[i : i + 2].strip()}
    candidates = _candidate_sentences(text)
    if not candidates:
        return text.strip()[:_MAX_SENTENCE_CHARS]
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (-sum(gram in item[1] for gram in grams), item[0]),
    )
    chosen = [candidates[index][:_MAX_SENTENCE_CHARS] for index, _ in ranked[:limit]]
    return "；".join(chosen)


def _grounded_answer(block: str, question: str) -> str:
    """Extractive answer assembled from the retrieved chunks, with citations."""
    if NO_CONTEXT_BODY in block:
        return (
            "当前知识库没有足够信息回答该问题。\n"
            "请先通过 POST /api/knowledge/ingest 导入相关公开资料，或换一种问法。"
        )
    entries = _parse_context(block)
    if not entries:
        return "当前知识库没有足够信息回答该问题。"
    lines = [
        f"根据知识库检索到的 {len(entries)} 条资料（MockProvider 抽取式回答，"
        "接入真实模型后由 LLM 生成自然语言总结）："
    ]
    for index, _label, text in entries[:_MAX_CITED_SOURCES]:
        lines.append(f"- {_best_sentences(text, question)} [{index}]")
    lines.append("")
    lines.append("引用来源：")
    for index, label, _text in entries:
        lines.append(f"[{index}] {label}")
    return "\n".join(lines)


class MockProvider(BaseProvider):
    """Deterministic mock provider for testing and offline development.

    Two behaviours:

    * plain chat -> canned responses keyed off the last user message;
    * RAG chat (prompt carries a 【知识库检索结果】 block) -> extractive answer
      built only from the retrieved chunks, with [n] citations.
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

        context_block = _find_rag_context(messages)
        if context_block is not None:
            content = _grounded_answer(context_block, user_msg)
        # Deterministic canned responses for demo scenarios
        elif "恒光" in user_msg and "业务" in user_msg:
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
