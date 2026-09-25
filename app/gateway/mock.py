"""MockProvider: deterministic responses so tests run without API keys.

Three behaviours:

* plain chat (no ``tools``) -> Day-1 canned responses keyed off the last user
  message, plus extractive answers for RAG prompts;
* agent chat (``tools`` given) -> deterministic tool calling: enterprise
  questions become a ``knowledge_search`` tool call, document lookups become
  ``document_lookup``, everything else is answered directly;
* scripted agent chat (``script`` given) -> replays a fixed queue of tool
  calls regardless of the message, which lets tests exercise loop limits.
"""

from __future__ import annotations

import re
import time
from typing import Any

from app.gateway.base import BaseProvider, ModelResponse, ToolCall
from app.rag.prompt import CONTEXT_HEADER, NO_CONTEXT_BODY

_CITATION_LINE_RE = re.compile(r"^\[(\d+)\]\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；])")
_MAX_CITED_SOURCES = 3
_MAX_SENTENCE_CHARS = 120

# Messages containing any of these terms are treated as enterprise-knowledge
# questions and answered with a knowledge_search tool call (agent mode only).
_ENTERPRISE_TERMS = (
    "恒光",
    "业务",
    "产品",
    "产能",
    "原材料",
    "采购",
    "价格",
    "营收",
    "营业收入",
    "净利润",
    "氯碱",
    "盐酸",
    "液碱",
    "次氯酸钠",
    "安全",
    "车间",
    "员工",
    "制度",
    "年报",
    "半年报",
    "上市",
)

# Day-4 business tools: fixed operation names the heuristic may choose.
ERP_TOOL = "erp_purchase_analysis"
SAFETY_TOOL = "safety_incident_analysis"

# Enterprise *data* questions go to the business tools before the knowledge base,
# because 采购/价格/安全 also appear in _ENTERPRISE_TERMS.
_ERP_TERMS = ("采购", "价格", "供应商", "订单", "库存", "物料", "原材料", "采购额", "花费")
_SAFETY_TERMS = ("安全", "事故", "隐患", "车间", "区域", "风险", "事件", "违章")

# Keyword -> document_id hints for scripted/heuristic document_lookup calls.
# 半年报 must be checked before 年报 (it contains that substring).
_DOCUMENT_HINTS: tuple[tuple[str, str], ...] = (
    ("半年报", "hengguang-half-year-report-2026"),
    ("年报", "hengguang-annual-report-2025"),
    ("产品", "hengguang-products-and-capacity"),
    ("产能", "hengguang-products-and-capacity"),
    ("安全", "hengguang-safety-production-2025"),
    ("上市", "hengguang-ipo-2021"),
    ("简介", "hengguang-public-profile"),
)
_DEFAULT_DOCUMENT_ID = "hengguang-public-profile"


def _find_rag_context(messages: list[dict[str, Any]]) -> str | None:
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

    Three behaviours, selected per call:

    * plain chat (``tools`` not given) -> Day-1 canned responses keyed off the
      last user message; RAG prompts (carrying a 【知识库检索结果】 block)
      get an extractive answer with [n] citations;
    * agent chat (``tools`` given) -> deterministic tool calling: enterprise
      questions become a knowledge_search call, document lookups become a
      document_lookup call, everything else is answered directly;
    * scripted agent chat (``script`` given) -> replays a fixed queue of tool
      names regardless of the message (loop-limit and failure-path tests).
    """

    def __init__(self, *, script: list[str] | None = None) -> None:
        """``script``: deterministic queue of tool names (or "final") to replay."""
        self._script = list(script) if script else []
        self._call_counter = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    async def _chat_impl(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float,
        response_format: dict | None,
        tools: list[dict] | None = None,
    ) -> ModelResponse:
        start = time.perf_counter()

        # Get the last user message
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "") or ""
                break

        if tools:
            tool_names = {str(tool.get("function", {}).get("name") or "") for tool in tools}
            content, tool_calls = self._agent_turn(messages, user_msg, tool_names)
        else:
            content, tool_calls = self._plain_turn(messages, user_msg), []

        latency_ms = int((time.perf_counter() - start) * 1000)

        return ModelResponse(
            content=content,
            model=model or "mock-model",
            provider=self.provider_name,
            usage={"prompt_tokens": len(user_msg), "completion_tokens": len(content)},
            latency_ms=latency_ms,
            tool_calls=tool_calls,
        )

    # ------------------------------------------------------------------
    # Agent mode (Day 3): deterministic tool calling
    # ------------------------------------------------------------------

    def _agent_turn(
        self, messages: list[dict[str, Any]], user_msg: str, tool_names: set[str]
    ) -> tuple[str, list[ToolCall]]:
        """One agent LLM round: scripted action first, then the heuristic decision."""
        if self._script:
            action = self._script.pop(0)
            if action != "final":
                return "", [self._make_tool_call(action, user_msg)]
        tool_content = _find_last_tool_content(messages)
        if tool_content is not None:
            # A tool already ran: the answer must be built from its result.
            return _answer_from_tool_result(tool_content, user_msg), []

        if self._wants_document_details(user_msg) and "document_lookup" in tool_names:
            return "", [self._make_tool_call("document_lookup", user_msg)]
        if self._wants_erp(user_msg) and ERP_TOOL in tool_names:
            return "", [self._make_tool_call(ERP_TOOL, user_msg)]
        if self._wants_safety(user_msg) and SAFETY_TOOL in tool_names:
            return "", [self._make_tool_call(SAFETY_TOOL, user_msg)]
        if self._wants_knowledge(user_msg) and "knowledge_search" in tool_names:
            return "", [self._make_tool_call("knowledge_search", user_msg)]
        if self._wants_document_lookup(user_msg) and "document_lookup" in tool_names:
            return "", [self._make_tool_call("document_lookup", user_msg)]
        return self._no_tool_answer(user_msg), []

    def _make_tool_call(self, name: str, user_msg: str) -> ToolCall:
        """Deterministic tool call: same message -> same name + arguments."""
        self._call_counter += 1
        if name == "knowledge_search":
            arguments: dict = {"query": user_msg}
        elif name == "document_lookup":
            arguments = {"document_id": _document_id_for(user_msg)}
        elif name == ERP_TOOL:
            arguments = {
                "operation": _erp_operation_for(user_msg),
                "days": _window_days(user_msg),
                "limit": 10,
            }
        elif name == SAFETY_TOOL:
            arguments = {
                "operation": _safety_operation_for(user_msg),
                "days": _window_days(user_msg),
                "limit": 10,
            }
        else:  # unknown tool on purpose (executor must reject it)
            arguments = {}
        return ToolCall(id=f"call_{name}_{self._call_counter}", name=name, arguments=arguments)

    @staticmethod
    def _wants_knowledge(user_msg: str) -> bool:
        return any(term in user_msg for term in _ENTERPRISE_TERMS)

    @staticmethod
    def _wants_erp(user_msg: str) -> bool:
        """Purchase / supplier / inventory question -> ERP tool."""

        return any(term in user_msg for term in _ERP_TERMS)

    @staticmethod
    def _wants_safety(user_msg: str) -> bool:
        """Safety incident / area / risk question -> safety tool."""

        return any(term in user_msg for term in _SAFETY_TERMS)

    @staticmethod
    def _wants_document_details(user_msg: str) -> bool:
        """Explicit request to inspect one document (查看…详细信息 / document)."""
        lowered = user_msg.lower()
        lookup_word = "查看" in user_msg or "文档" in user_msg or "document" in lowered
        detail_word = "详细信息" in user_msg or "详情" in user_msg or "document" in lowered
        return lookup_word and detail_word

    @staticmethod
    def _wants_document_lookup(user_msg: str) -> bool:
        lowered = user_msg.lower()
        return "查看" in user_msg or "文档" in user_msg or "document" in lowered

    @staticmethod
    def _no_tool_answer(user_msg: str) -> str:
        """Final answer when no tool is needed: Day-1 canned replies, policy fallback."""
        if "你好" in user_msg or "hello" in user_msg.lower():
            return "你好！我是恒光 AI 平台的模拟助手。有什么可以帮您的吗？"
        return (
            "我是恒光 AI 平台的企业助手。这个问题不需要查询企业知识库，"
            "我不会编造企业事实；当前知识库没有足够信息支撑这个请求。"
        )

    # ------------------------------------------------------------------
    # Plain mode (Day 1, unchanged)
    # ------------------------------------------------------------------

    def _plain_turn(self, messages: list[dict[str, Any]], user_msg: str) -> str:
        context_block = _find_rag_context(messages)
        if context_block is not None:
            return _grounded_answer(context_block, user_msg)
        # Deterministic canned responses for demo scenarios
        if "恒光" in user_msg and "业务" in user_msg:
            return (
                "根据公开资料，湖南恒光科技股份有限公司主要从事无机精细化学品的研发、生产和销售，"
                "核心产品包括氯碱系列产品（如盐酸、液碱、次氯酸钠等）以及相关化工新材料。"
                "公司在化工行业有一定的市场地位，持续进行技术创新和产能优化。"
            )
        if "采购" in user_msg and "价格" in user_msg:
            return (
                "基于合成 ERP 数据分析，最近 30 天主要原材料采购价格呈现小幅波动："
                "盐酸均价约 320 元/吨（+2.1%），液碱均价约 1850 元/吨（-1.3%），"
                "次氯酸钠均价约 680 元/吨（+0.8%）。整体趋势相对平稳。"
            )
        if "安全" in user_msg and ("区域" in user_msg or "车间" in user_msg):
            return (
                "根据合成安全事件数据，最近一个月 A 车间记录 12 起安全事件（占比 40%），"
                "B 车间 7 起，C 车间 5 起。A 车间主要为操作规程违规和设备隐患，"
                "建议重点加强岗前培训和设备巡检。"
            )
        if "你好" in user_msg or "hello" in user_msg.lower():
            return "你好！我是恒光 AI 平台的模拟助手。有什么可以帮您的吗？"
        return f"[Mock] 收到您的消息：{user_msg[:100]}"


def _find_last_tool_content(messages: list[dict[str, Any]]) -> str | None:
    """Content of the most recent tool-result message, if the loop already ran one."""
    for msg in reversed(messages):
        if msg.get("role") == "tool":
            return msg.get("content") or ""
    return None


def _answer_from_tool_result(content: str, question: str) -> str:
    """Final answer built only from the tool result, never from thin air."""
    if content.startswith(CONTEXT_HEADER):
        # knowledge_search results reuse the RAG context block: extractive
        # answer with [n] citations, or the explicit no-information message.
        return _grounded_answer(content, question)
    cleaned = content.strip()
    if not cleaned:
        return "当前知识库没有足够信息回答该问题。"
    return cleaned  # tool content is already user-facing (e.g. document summary)


_DAYS_RE = re.compile(r"(\d+)\s*(?:天|日|days?)")
_DEFAULT_WINDOW_DAYS = 30

_ERP_OPERATIONS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("库存", "仓储", "存货"), "inventory_summary"),
    (("供应商", "供货"), "supplier_summary"),
    (("订单",), "recent_purchase_orders"),
    (("趋势", "变化", "涨", "跌", "价格"), "purchase_price_trend"),
    (("排名", "前几", "花费", "金额", "采购额", "主要"), "top_materials_by_spend"),
)

_SAFETY_OPERATIONS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("等级", "严重", "分级"), "incident_by_severity"),
    (("类别", "原因", "类型", "隐患"), "incident_by_category"),
    (("趋势", "走势", "每周", "按月"), "incident_trend"),
    (("高风险", "重大", "危险"), "recent_high_risk"),
    (("区域", "车间", "哪个", "分布", "最多"), "incident_by_area"),
)


def _window_days(user_msg: str) -> int:
    """Extract an analysis window in days (最近30天 / 一个月 / default 30)."""

    match = _DAYS_RE.search(user_msg)
    if match:
        return max(1, min(365, int(match.group(1))))
    if "一个月" in user_msg or "本月" in user_msg:
        return 30
    if "一周" in user_msg or "本周" in user_msg:
        return 7
    if "季度" in user_msg or "三个月" in user_msg:
        return 90
    if "半年" in user_msg:
        return 180
    if "一年" in user_msg:
        return 365
    return _DEFAULT_WINDOW_DAYS


def _operation_for(
    user_msg: str, table: tuple[tuple[tuple[str, ...], str], ...], default: str
) -> str:
    for terms, operation in table:
        if any(term in user_msg for term in terms):
            return operation
    return default


def _erp_operation_for(user_msg: str) -> str:
    return _operation_for(user_msg, _ERP_OPERATIONS, "purchase_price_trend")


def _safety_operation_for(user_msg: str) -> str:
    return _operation_for(user_msg, _SAFETY_OPERATIONS, "incident_by_area")


def _document_id_for(user_msg: str) -> str:
    """Deterministic document_id from keyword hints, defaulting to the profile."""
    for keyword, document_id in _DOCUMENT_HINTS:
        if keyword in user_msg:
            return document_id
    return _DEFAULT_DOCUMENT_ID
