"""Runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Flat settings for the demo platform.

    Defaults use mock providers so a fresh clone runs without any API keys.
    """

    app_version: str = field(default_factory=lambda: os.environ.get("APP_VERSION", "0.1.0"))
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "mock"))
    llm_base_url: str = field(default_factory=lambda: os.environ.get("LLM_BASE_URL", ""))
    llm_api_key: str = field(default_factory=lambda: os.environ.get("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.environ.get("LLM_MODEL", ""))
    embedding_provider: str = field(
        default_factory=lambda: os.environ.get("EMBEDDING_PROVIDER", "mock")
    )
    embedding_base_url: str = field(
        default_factory=lambda: os.environ.get("EMBEDDING_BASE_URL", "")
    )
    embedding_api_key: str = field(default_factory=lambda: os.environ.get("EMBEDDING_API_KEY", ""))
    embedding_model: str = field(default_factory=lambda: os.environ.get("EMBEDDING_MODEL", ""))
    database_url: str = field(
        default_factory=lambda: os.environ.get("DATABASE_URL", "sqlite:///./data/runtime/app.db")
    )
    chroma_path: str = field(
        default_factory=lambda: os.environ.get("CHROMA_PATH", "./data/runtime/chroma")
    )

    @property
    def is_mock_llm(self) -> bool:
        return self.llm_provider == "mock"


settings = Settings()
