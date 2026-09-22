"""Model Gateway package: unified LLM access. Business code must only use ModelGateway."""

from app.gateway.base import ModelProvider, ModelResponse
from app.gateway.router import ModelGateway, gateway

__all__ = ["ModelProvider", "ModelResponse", "ModelGateway", "gateway"]
