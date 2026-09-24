"""Whitelisted tool registry contents (Day 3: knowledge_search + document_lookup)."""

from __future__ import annotations

from app.agent.registry import ToolRegistry
from app.agent.tools.base import Tool, ToolResult
from app.agent.tools.document import DocumentLookupTool
from app.agent.tools.knowledge import KnowledgeSearchTool
from app.services.knowledge_service import KnowledgeService

__all__ = [
    "DocumentLookupTool",
    "KnowledgeSearchTool",
    "Tool",
    "ToolResult",
    "build_default_registry",
]


def build_default_registry(knowledge_service: KnowledgeService) -> ToolRegistry:
    """Day-3 tool whitelist: knowledge_search + document_lookup."""
    registry = ToolRegistry()
    registry.register(KnowledgeSearchTool(knowledge_service))
    registry.register(DocumentLookupTool(knowledge_service))
    return registry
