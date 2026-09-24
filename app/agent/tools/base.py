"""Tool contract: Tool protocol + ToolResult (Day 3).

A tool is the single source of truth for its name, description, parameter
schema and argument validation: the LLM-facing JSON schema is generated from
``args_model``, never hand-written a second time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass
class ToolResult:
    """Uniform tool outcome.

    * ``success`` distinguishes tool success from failure;
    * Python exceptions never escape: they are converted into a controlled
      ``error`` string by the executor;
    * failures are still returned to the agent, which can retry or change path;
    * ``metadata`` carries retrieval info (sources, scores) through the agent.
    """

    tool_name: str
    success: bool
    content: str
    metadata: dict = field(default_factory=dict)
    error: str | None = None


class Tool(ABC):
    """Whitelisted business tool.

    Subclasses set ``name`` / ``description`` / ``args_model`` and implement
    ``execute``. Validation happens via ``validate`` so the executor stays
    business-agnostic.
    """

    name: str
    description: str
    args_model: type[BaseModel]

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
