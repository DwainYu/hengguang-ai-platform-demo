"""Agent service: wires the runtime, the tool registry and the model gateway.

API endpoints depend on this class (via ``get_agent_service``), so tests can
inject a knowledge service + gateway without touching global settings.
"""

from __future__ import annotations

from app.agent.models import AgentRunResult
from app.agent.registry import ToolRegistry
from app.agent.runtime import AgentRuntime
from app.agent.tools import build_default_registry
from app.config import Settings, settings
from app.gateway.router import ModelGateway
from app.gateway.router import gateway as default_gateway
from app.services.knowledge_service import KnowledgeService, get_knowledge_service


class AgentService:
    """One object that owns the Day-3 agent use cases.

    Two clear entries exist (Day 3):

    * ``POST /api/chat``      -> Model Gateway (direct, Day-1 behaviour);
    * ``POST /api/agent/run`` -> AgentService -> AgentRuntime -> Model Gateway
      -> Tool Registry -> Knowledge Search -> RAG -> Citation.
    """

    def __init__(
        self,
        *,
        gateway: ModelGateway | None = None,
        knowledge_service: KnowledgeService | None = None,
        config: Settings | None = None,
    ) -> None:
        self.config = config or settings
        self.gateway = gateway or default_gateway
        self.knowledge = knowledge_service or get_knowledge_service()
        self.registry: ToolRegistry = build_default_registry(self.knowledge)
        self.runtime = AgentRuntime(self.gateway, self.registry, config=self.config)

    @property
    def tool_names(self) -> list[str]:
        return self.registry.names()

    async def run(self, message: str, *, max_steps: int | None = None) -> AgentRunResult:
        """Run the agent loop for one user message."""
        return await self.runtime.run(message, max_steps=max_steps)


_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Process-wide agent service (built from settings on first use)."""
    global _service
    if _service is None:
        _service = AgentService()
    return _service


def set_agent_service(service: AgentService | None) -> None:
    """Override the service instance (used by tests and dependency injection)."""
    global _service
    _service = service
