"""Tool contract: Tool protocol + ToolResult (Day 3).

A tool is the single source of truth for its name, description, parameter
schema and argument validation: the LLM-facing JSON schema is generated from
``args_model``, never hand-written a second time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.auth.permissions import Permission


@dataclass
class ToolResult:
    """Uniform tool outcome.

    * ``success`` distinguishes tool success from failure;
    * Python exceptions never escape: they are converted into a controlled
      ``error`` string by the executor;
    * failures are still returned to the agent, which can retry or change path;
    * ``metadata`` carries retrieval info (sources, scores) through the agent;
    * ``error_code`` (Day 4) is the machine-readable twin of ``error``, e.g.
      ``PERMISSION_DENIED`` — ``error_detail`` renders the ``{"code", "message"}``
      object the platform API and audit trail use.
    """

    tool_name: str
    success: bool
    content: str
    metadata: dict = field(default_factory=dict)
    error: str | None = None
    error_code: str | None = None

    @property
    def error_detail(self) -> dict | None:
        """``{"code": ..., "message": ...}`` for failures, ``None`` on success."""

        if self.success:
            return None
        return {
            "code": self.error_code or "TOOL_ERROR",
            "message": self.error or "工具执行失败",
        }

    @property
    def payload(self) -> dict:
        """Structured tool output (``{"success", "operation", "days", "data"}``)."""

        return self.metadata.get("payload", {})


class Tool(ABC):
    """Whitelisted business tool.

    Subclasses set ``name`` / ``description`` / ``args_model`` and implement
    ``execute``. Validation happens via ``validate`` so the executor stays
    business-agnostic.
    """

    name: str
    description: str
    args_model: type[BaseModel]
    #: Permission needed to execute this tool. Defaults to "just run the agent",
    #: so generic/Day-3 tools keep working for every demo role; business tools
    #: override it (``tool:erp`` / ``tool:safety``) and the ToolExecutor enforces it.
    permission: Permission | str = Permission.AGENT_RUN

    @property
    def parameters(self) -> dict:
        """JSON-schema parameters, generated from ``args_model``."""
        schema = self.args_model.model_json_schema()
        schema.pop("title", None)
        return schema

    def validate(self, arguments: dict) -> dict:
        """Validate and normalize arguments; raises pydantic ValidationError."""
        return self.args_model.model_validate(arguments).model_dump()

    def to_openai_schema(self) -> dict:
        """OpenAI function-calling schema (single source of truth)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    async def execute(self, arguments: dict) -> ToolResult: ...
