"""Runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


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
    # Embedding / RAG tuning (SPEC section 6.2 / 6.3)
    embedding_dimensions: int = field(
        default_factory=lambda: _env_int("EMBEDDING_DIMENSIONS", 1024)
    )
    documents_dir: str = field(
        default_factory=lambda: _env_str("DOCUMENTS_DIR", "./data/documents")
    )
    chroma_collection: str = field(
        default_factory=lambda: _env_str("CHROMA_COLLECTION", "hengguang_knowledge")
    )
    rag_chunk_size: int = field(default_factory=lambda: _env_int("RAG_CHUNK_SIZE", 1000))
    rag_chunk_overlap: int = field(default_factory=lambda: _env_int("RAG_CHUNK_OVERLAP", 150))
    rag_top_k: int = field(default_factory=lambda: _env_int("RAG_TOP_K", 5))
    # A chunk is used as RAG context only above this fused similarity score
    rag_min_score: float = field(
        default_factory=lambda: float(os.environ.get("RAG_MIN_SCORE", "0.10"))
    )

    @property
    def is_mock_llm(self) -> bool:
        return self.llm_provider == "mock"

    @property
    def is_mock_embedding(self) -> bool:
        return self.embedding_provider == "mock"


settings = Settings()
