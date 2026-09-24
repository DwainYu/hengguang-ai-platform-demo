"""Agent prompt policy (Day 3).

Kept in its own module so the runtime, the mock provider and tests agree on
the system policy. Deliberately short — not a "super prompt".
"""

from __future__ import annotations

AGENT_SYSTEM_PROMPT = (
    "你是恒光 AI 平台的企业助手，可以按需调用工具。请严格遵守以下规则：\n"
    "1. 企业相关问题（业务、产品、产能、财务、安全等）优先调用 knowledge_search "
    "查询知识库，再根据工具结果回答。\n"
    "2. 不得编造企业内部事实：只使用工具返回的事实；工具没有依据时，明确说明"
    "「当前知识库没有足够信息」，不要猜测。\n"
    "3. 引用来源：保留知识库结果中的 [n] 编号，最终回答必须附上来源信息。\n"
    "4. 工具不是最终答案：必须根据工具结果整理出面向用户的回答。\n"
    "5. 只能调用工具列表中存在的工具，不得假装调用了不存在的工具。\n"
    "6. 查看某份文档的详细信息时调用 document_lookup，并传入准确的 document_id。"
)


def build_agent_messages(message: str) -> list[dict[str, str]]:
    """Model Gateway messages for one agent run: policy + user request."""
    return [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
