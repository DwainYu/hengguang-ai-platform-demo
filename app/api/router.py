"""API router assembly (kept out of ``app/api/__init__.py`` on purpose).

Importing a leaf module such as :mod:`app.api.errors` must never pull in the whole
router stack — the agent layer depends on the error types, and the routers depend
on the agent layer, so eager router imports in the package ``__init__`` would be a
circular import.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.agents import router as agents_router
from app.api.audit import router as audit_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.metrics import router as metrics_router
from app.api.models import router as models_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(agents_router)
api_router.include_router(models_router)
api_router.include_router(audit_router)
api_router.include_router(metrics_router)
api_router.include_router(users_router)

__all__ = ["api_router"]
