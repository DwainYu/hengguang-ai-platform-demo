"""FastAPI application entry point.

Day-4 wiring on top of the Day-1/2/3 app: structured logging, the request-id +
metrics middleware, the unified error handlers, and a lifespan that prepares the
synthetic SQLite business data so the ERP / safety tools have something to query on
the very first request.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.config import get_settings
from app.db.database import get_database
from app.db.seed import ensure_seeded
from app.observability.logging import configure_logging
from app.observability.middleware import RequestContextMiddleware

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Prepare logging and the synthetic demo database before serving requests."""

    settings = get_settings()
    configure_logging()
    database = get_database()
    database.initialize()
    seeded = ensure_seeded(database)
    logger.info(
        "hengguang demo platform started",
        extra={
            "event": "app.start",
            "version": settings.app_version,
            "db_path": database.path,
            "seeded": seeded or "already-seeded",
        },
    )
    yield
    logger.info("hengguang demo platform stopped", extra={"event": "app.stop"})


settings = get_settings()
app = FastAPI(
    title="Hengguang AI Platform Demo",
    version=settings.app_version,
    description=(
        "Minimal enterprise AI platform prototype: Model Gateway, RAG, tool-calling "
        "Agent Runtime, RBAC, audit log and observability. All business data shown in "
        "this demo is synthetic (data/synthetic), not real enterprise data."
    ),
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(api_router)
