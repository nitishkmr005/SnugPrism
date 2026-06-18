from pathlib import Path
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_FILE = Path(__file__).parent / "app.yaml"


def _load_yaml() -> dict:
    with open(_CONFIG_FILE) as f:
        return yaml.safe_load(f)


_cfg = _load_yaml()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = _cfg["app"]["name"]
    app_host: str = _cfg["app"]["host"]
    app_port: int = _cfg["app"]["port"]
    app_version: str = _cfg["app"]["version"]

    # CORS — comma-separated override via CORS_ORIGINS env var; defaults from yaml
    cors_origins_raw: str = ",".join(_cfg["cors"]["origins"])

    # LLM
    llm_provider: str = _cfg["llm"]["provider"]
    openai_model: str = _cfg["llm"]["model"]
    qa_model: str = _cfg["llm"]["qa_model"]
    codex_qa_model: str = "gpt-5.3-codex"
    llm_max_tokens: int = _cfg["llm"]["max_tokens"]

    # Embeddings
    embedding_provider: str = _cfg["embeddings"]["provider"]
    embedding_model: str = _cfg["embeddings"]["model"]
    embedding_dimension: int = _cfg["embeddings"]["dimension"]

    # RAG
    rag_top_k: int = _cfg["rag"]["top_k"]
    rag_chunk_size: int = _cfg["rag"]["chunk_size"]
    rag_chunk_overlap: int = _cfg["rag"]["chunk_overlap"]
    web_search_max_results: int = _cfg["rag"]["web_search_max_results"]
    qa_context_chars: int = 8000
    qa_questions_per_window: int = 3
    qa_max_windows: int = 0  # 0 means use every context window

    # Logging
    log_level: str = _cfg["logging"]["level"]

    # Qdrant — host/port for local; set QDRANT_URL + QDRANT_API_KEY for cloud
    qdrant_host: str = _cfg["qdrant"]["host"]
    qdrant_port: int = _cfg["qdrant"]["port"]
    qdrant_collection: str = _cfg["qdrant"]["collection"]
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    # MongoDB — full URI in .env (may contain credentials for Atlas)
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = _cfg["mongodb"]["database"]

    # Secrets — from .env only
    openai_api_key: str = ""
    tavily_api_key: str | None = None
    voice_agent_api_key: str = ""

    # Paths
    pdfs_dir: Path = Path("data/pdfs")
    logs_dir: Path = Path("logs")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
