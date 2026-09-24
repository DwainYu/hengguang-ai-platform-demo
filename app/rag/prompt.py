"""RAG prompt contract: the context block format and the answer policy.

Kept in its own module because both sides need it: the pipeline builds the
block, and `MockProvider` recognises it to behave like a grounded assistant.
"""

from __future__ import annotations

from app.rag.schemas import Citation, RetrievedChunk

CONTEXT_HEADER = "【知识库检索结果】"
NO_CONTEXT_BODY = "（当前知识库没有检索到与该问题相关的资料）"

# SPEC section 6.4 — answer policy that every RAG prompt must carry.
RAG_SYSTEM_PROMPT = (
    "你是恒光 AI 平台的企业知识助手。请严格遵守以下回答规则：\n"
    "1. 优先依据【知识库检索结果】中的资料回答，只使用资料中出现的事实。\n"
    "2. 如果资料不足以回答，明确说明「当前知识库没有足够信息」，不要编造数据。\n"
    "3. 不得虚构任何数字、产能、财务指标或产品名称。\n"
    "4. 使用 [编号] 标注引用来源，编号与【知识库检索结果】中的编号一致。\n"
    "5. 区分事实（来自资料）、推测（基于事实的判断）与建议（你的观点），"
    "对推测和建议要明确说明。\n"
    "6. 本项目只使用公开资料，回答不构成投资建议。"
)


def format_context(results: list[RetrievedChunk], citations: list[Citation]) -> str:
    """Render retrieved chunks as a numbered, citable context block."""
    if not results:
        return f"{CONTEXT_HEADER}\n{NO_CONTEXT_BODY}"
    lines = [CONTEXT_HEADER]
    for citation, result in zip(citations, results, strict=True):
        lines.append(f"{citation.marker} {citation.label}")
        lines.append(result.content)
        lines.append("")
    return "\n".join(lines).rstrip()


def build_messages(
    question: str, results: list[RetrievedChunk], citations: list[Citation]
) -> list[dict[str, str]]:
    """Model Gateway messages: answer policy + retrieved context + question."""
    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "system", "content": format_context(results, citations)},
        {"role": "user", "content": question},
    ]
