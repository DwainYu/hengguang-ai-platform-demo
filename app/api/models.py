"""GET /api/models — configured providers and models (Day 4 §十四).

The response describes *availability* only: no API key, base URL, token or other
environment value is included (a Day-1 regression test asserts exactly that, and it
stays true now that RBAC guards the endpoint too).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.errors import ProviderError
from app.auth.auth import CurrentUser
from app.auth.dependencies import require
from app.auth.permissions import Permission, permissions_for_role
from app.gateway.router import gateway
from app.observability.middleware import request_id_of
from app.services.agent_service import AgentService, get_agent_service

router = APIRouter(prefix="/api", tags=["models"])


class ModelInfo(BaseModel):
    provider: str
    model: str
    available: bool
    default: bool = False
    kind: str = "chat"


class ModelsResponse(BaseModel):
    request_id: str = ""
    models: list[ModelInfo] = []
    agent: dict = {}
    permissions: list[str] = []


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    request_id: Annotated[str, Depends(request_id_of)],
    user: Annotated[CurrentUser, Depends(require(Permission.MODELS_LIST))],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> ModelsResponse:
    """Model/provider availability plus the caller's own permissions."""

    try:
        entries = gateway.list_models()
    except Exception as error:  # pragma: no cover - defensive: gateway construction
        raise ProviderError(
            "模型目录暂不可用", details={"error_type": type(error).__name__}
        ) from error
    return ModelsResponse(
        request_id=request_id,
        models=[ModelInfo(**entry) for entry in entries],
        agent={
            "tools": service.registry.names(),
            "allowed_tools": service.tools_allowed_for(user.role),
            "max_steps": service.runtime.max_steps,
            "max_tool_calls": service.runtime.max_tool_calls,
        },
        permissions=sorted(str(item) for item in permissions_for_role(user.role)),
    )
