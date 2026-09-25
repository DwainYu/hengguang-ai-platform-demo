"""Tool whitelist for the agent runtime (Day 3 knowledge tools + Day 4 business tools).

``build_default_registry`` is the single place where the platform decides which
tools an agent may even see: knowledge retrieval, document lookup, ERP purchase
analysis and safety incident analysis. Duplicate names are rejected by the
registry, and permissions (``tool:erp`` / ``tool:safety``) are enforced by the
:class:`~app.agent.executor.ToolExecutor` — not here.
"""

from __future__ import annotations

from app.agent.registry import ToolRegistry
from app.agent.tools.base import Tool, ToolResult
from app.agent.tools.business import BusinessOperation, BusinessQueryTool
from app.agent.tools.document import DocumentLookupTool
from app.agent.tools.erp import ErpPurchaseAnalysisTool
from app.agent.tools.knowledge import KnowledgeSearchTool
from app.agent.tools.safety import SafetyIncidentAnalysisTool
from app.db.database import Database
from app.services.knowledge_service import KnowledgeService

#: Exactly the tools the demo agent is allowed to use.
DEFAULT_TOOL_NAMES = (
    "knowledge_search",
    "document_lookup",
    "erp_purchase_analysis",
    "safety_incident_analysis",
)


def build_default_registry(
    knowledge_service: KnowledgeService,
    *,
    database: Database | None = None,
) -> ToolRegistry:
    """Build the Day-4 tool whitelist (4 tools, fixed operations, RBAC-tagged)."""

    registry = ToolRegistry()
    registry.register(KnowledgeSearchTool(knowledge_service))
    registry.register(DocumentLookupTool(knowledge_service))
    registry.register(ErpPurchaseAnalysisTool(database))
    registry.register(SafetyIncidentAnalysisTool(database))
    return registry


__all__ = [
    "DEFAULT_TOOL_NAMES",
    "BusinessOperation",
    "BusinessQueryTool",
    "DocumentLookupTool",
    "ErpPurchaseAnalysisTool",
    "KnowledgeSearchTool",
    "SafetyIncidentAnalysisTool",
    "Tool",
    "ToolResult",
    "build_default_registry",
]
