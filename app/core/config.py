"""
Application configuration via environment variables.
Aligns with docs/05-deployment-runbook.md.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    # Upload & parser (PRD §7.2 APP-01)
    UPLOAD_MAX_FILE_SIZE_MB: int = 50
    UPLOAD_MAX_FILES: int = 10
    PARSER_TIMEOUT_SECONDS: int = 120

    # LLM
    LLM_PROVIDER: Literal[
        "openai",
        "anthropic",
        "qwen",
        "deepseek",
        "openai_compatible",
        "local_openai",
        "ollama",
    ] = "ollama"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    COMPAT_API_KEY: str = ""
    COMPAT_BASE_URL: str = ""
    COMPAT_MODEL: str = ""
    LOCAL_API_KEY: str = ""
    LOCAL_BASE_URL: str = "http://localhost:1234/v1"
    LOCAL_MODEL: str = "local-model"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Parser engine: "docling", "legacy", or "auto" (docling with fallback)
    PARSER_ENGINE: Literal["docling", "legacy", "auto"] = "auto"

    # Vector / KB
    VECTOR_STORE_TYPE: Literal["chroma"] = "chroma"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    KB_AUTO_SYNC_DIR: str = "./examples"
    KB_AUTO_SYNC_INTERVAL_SECONDS: int = 0
    KB_REINDEX_ROOTS: str = "./examples"

    # Graph RAG (LightRAG)
    ENABLE_GRAPH_RAG: bool = True
    LIGHTRAG_WORKING_DIR: str = "./data/lightrag"
    GRAPH_RAG_QUERY_MODE: Literal["naive", "local", "global", "hybrid"] = "hybrid"

    # Review Console (optional shared token)
    REVIEW_CONSOLE_TOKEN: str = ""

    # MCP document access. Colon-separated on macOS/Linux, semicolon on Windows.
    MCP_DOCUMENT_ROOTS: str = "./examples"

    @property
    def upload_max_bytes(self) -> int:
        return self.UPLOAD_MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [
            value.strip() for value in self.CORS_ORIGINS.split(",") if value.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
