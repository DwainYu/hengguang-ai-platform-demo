"""Agent service: wires the runtime, the tool registry, RBAC and the model gateway.

API endpoints depend on this class (via ``get_agent_service``), so tests can inject
a knowledge service + gateway + database without touching global settings.

Day-4 platform flow (ARCHITECTURE.md):
``User → Auth → API → Agent → Permission → Tool → Data → Audit``.
"""

from __future__ import annotations

from app.agent.models import AgentRunResult
from app.agent.registry import ToolRegistry
from app.agent.runtime import AgentRuntime
from app.agent.tools import build_default_registry
from app.auth.permissions import allowed_tool_names
from app.config import Settings, get_settings
from app.db.database import Database
from app.gateway.router import ModelGateway
from app.gateway.router import gateway as default_gateway
from app.observability.audit import Actor, AuditLog, get_audit_log
from app.observability.metrics import metrics
from app.services.knowledge_service import KnowledgeService, get_knowledge_service


class AgentService:
    """One object that owns the agent use cases of the platform.

    Two clear entries exist:

    * ``POST /api/chat``       -> Model Gateway (direct, Day-1 behaviour);
    * ``POST /api/agent/run``  -> AgentService -> AgentRuntime -> Model Gateway
      -> Tool Registry -> **permission check** -> Tool -> synthetic data -> Audit.
    """

    def __init__(
        self,
        *,
        gateway: ModelGateway | None = None,
        knowledge_service: KnowledgeService | None = None,
        config: Settings | None = None,
        database: Database | None = None,
        audit: AuditLog | None = None,
    ) -> None:
        self.config = config or get_settings()
        self.gateway = gateway or default_gateway
        self.knowledge = knowledge_service or get_knowledge_service()
        self.audit = audit if audit is not None else get_audit_log()
        self.registry: ToolRegistry = build_default_registry(self.knowledge, database=database)
        self.runtime = AgentRuntime(
            self.gateway,
            self.registry,
            config=self.config,
            audit=self.audit,
        )

    @property
    def tool_names(self) -> list[str]:
        return self.registry.names()

    def tools_allowed_for(self, role: str | None) -> list[str]:
        """Tool names this role may execute (used by the API/docs and the Day-5 UI)."""

        return allowed_tool_names(role, self.registry.names())

    async def run(
        self,
        message: str,
        *,
        actor: Actor | None = None,
        max_steps: int | None = None,
        max_tool_calls: int | None = None,
    ) -> AgentRunResult:
        """Run one agent loop for ``message`` on behalf of ``actor``."""

        result = await self.runtime.run(
            message,
            max_steps=max_steps,
            max_tool_calls=max_tool_calls,
            actor=actor,
        )
        metrics.observe_agent_run(status=result.status)
        return result


_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Process-wide agent service (overridable in tests via dependency overrides)."""

    global _service
    if _service is None:
        _service = AgentService()
    return _service


def set_agent_service(service: AgentService | None) -> None:
    """Replace the process-wide agent service (tests / custom wiring)."""

    global _service
    _service = service
