"""GET /api/models — configured LLM providers (never returns API keys)."""

from fastapi import APIRouter

from app.gateway.router import gateway

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models")
async def list_models() -> dict:
    """Return configured model providers (no API keys)."""
    return {"models": gateway.list_models()}
