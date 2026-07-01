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
    AGENT_LLM_MODE: Literal["", "anthropic_compat"] = ""
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
    ANTHROPIC_AUTH_TOKEN: str = ""
    ANTHROPIC_DEFAULT_OPUS_MODEL: str = "claude-3-opus-latest"
    ANTHROPIC_DEFAULT_SONNET_MODEL: str = "claude-3-5-sonnet-latest"
    ANTHROPIC_DEFAULT_HAIKU_MODEL: str = "claude-3-5-haiku-latest"
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
    LLM_CONFIG_FILE: str = "./llm_config.json"

    # Governance and optional infrastructure
    POLICY_PACK_ID: str = "generic-ssdlc"
    POLICY_PACKS_DIR: str = "./policy_packs"
    POLICY_PACKS_OVERLAY_DIR: str = ""
    REDIS_URL: str = ""
    ENABLE_METRICS: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./database.db"
    ENABLE_CREATE_ALL: bool = True
    INITIAL_ADMIN_EMAIL: str = "admin@example.com"
    INITIAL_ADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_FULL_NAME: str = "System Admin"
    INITIAL_CLIENT_EMAIL: str = "client@example.com"
    INITIAL_CLIENT_PASSWORD: str = ""
    INITIAL_CLIENT_FULL_NAME: str = "Client User"
    INITIAL_SECURITY_EMAIL: str = "security@example.com"
    INITIAL_SECURITY_PASSWORD: str = ""
    INITIAL_SECURITY_FULL_NAME: str = "Security Reviewer"
    INITIAL_APPROVER_EMAIL: str = "approver@example.com"
    INITIAL_APPROVER_PASSWORD: str = ""
    INITIAL_APPROVER_FULL_NAME: str = "Security Approver"

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

    # Agent interoperability gateway. Without a token, protocol endpoints only
    # accept loopback clients.
    AGENT_GATEWAY_ENABLED: bool = True
    AGENT_GATEWAY_TOKEN: str = ""
    AGENT_GATEWAY_PUBLIC_URL: str = "http://localhost:8000"
    AGENT_GATEWAY_ALLOWED_HOSTS: str = "127.0.0.1:*,localhost:*,[::1]:*"
    AGENT_GATEWAY_ALLOWED_ORIGINS: str = "http://127.0.0.1:*,http://localhost:*"
    AGENT_GATEWAY_TASK_TIMEOUT_SECONDS: int = 300

    def __init__(self, **values):
        super().__init__(**values)
        self._validate_production_security()

    def _validate_production_security(self) -> None:
        if self.ENV.strip().lower() not in {"production", "prod"}:
            return

        secret = self.SECRET_KEY.strip()
        if not secret or secret == "change-me-in-production" or len(secret) < 32:
            raise RuntimeError(
                "SECRET_KEY must be set to a random value of at least 32 "
                "characters in production."
            )
        if self.AGENT_GATEWAY_ENABLED and not self.AGENT_GATEWAY_TOKEN.strip():
            raise RuntimeError(
                "AGENT_GATEWAY_TOKEN is required when AGENT_GATEWAY_ENABLED is "
                "true in production."
            )

    @property
    def upload_max_bytes(self) -> int:
        return self.UPLOAD_MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [
            value.strip() for value in self.CORS_ORIGINS.split(",") if value.strip()
        ]

    @property
    def agent_gateway_allowed_hosts(self) -> list[str]:
        return [
            value.strip()
            for value in self.AGENT_GATEWAY_ALLOWED_HOSTS.split(",")
            if value.strip()
        ]

    @property
    def agent_gateway_allowed_origins(self) -> list[str]:
        return [
            value.strip()
            for value in self.AGENT_GATEWAY_ALLOWED_ORIGINS.split(",")
            if value.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
