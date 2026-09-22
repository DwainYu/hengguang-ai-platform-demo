"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api import api_router

app = FastAPI(
    title="Hengguang AI Platform Demo",
    version="0.1.0",
    description="Minimal enterprise AI platform prototype "
    "(Model Gateway, RAG, Agent, RBAC, Audit).",
)
app.include_router(api_router)
