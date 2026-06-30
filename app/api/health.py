"""Health and runtime configuration endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import llm_config_store

router = APIRouter(tags=["health"])

LLMProvider = (
    "openai",
    "anthropic",
    "qwen",
    "deepseek",
    "openai_compatible",
    "local_openai",
    "ollama",
)


class LLMConfigUpdate(BaseModel):
    provider: str = Field(..., description="LLM provider id")
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    agent_llm_mode: str | None = None
    anthropic_auth_token: str | None = None


def _mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _provider_values(provider: str) -> tuple[str, str, str]:
    return llm_config_store.provider_values(provider)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/config/llm")
async def config_llm():
    """Current LLM config with secrets masked."""
    model, base_url, api_key = _provider_values(settings.LLM_PROVIDER)
    return {
        "provider": settings.LLM_PROVIDER,
        "agent_llm_mode": settings.AGENT_LLM_MODE,
        "model": model,
        "base_url": base_url,
        "api_key_set": bool(api_key),
        "api_key_preview": _mask_secret(api_key),
        "providers": [
            {
                "id": "openai",
                "label": "OpenAI",
                "default_model": "gpt-4o-mini",
                "default_base_url": "",
                "requires_api_key": True,
            },
            {
                "id": "anthropic",
                "label": "Anthropic Claude",
                "default_model": "claude-3-5-sonnet-latest",
                "default_base_url": "",
                "requires_api_key": True,
            },
            {
                "id": "qwen",
                "label": "Qwen / DashScope",
                "default_model": "qwen-plus",
                "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "requires_api_key": True,
            },
            {
                "id": "deepseek",
                "label": "DeepSeek",
                "default_model": "deepseek-chat",
                "default_base_url": "https://api.deepseek.com",
                "requires_api_key": True,
            },
            {
                "id": "openai_compatible",
                "label": "OpenAI-compatible API",
                "default_model": "",
                "default_base_url": "",
                "requires_api_key": True,
            },
            {
                "id": "local_openai",
                "label": "Local OpenAI-compatible API",
                "default_model": "local-model",
                "default_base_url": "http://localhost:1234/v1",
                "requires_api_key": False,
            },
            {
                "id": "ollama",
                "label": "Ollama",
                "default_model": "llama2",
                "default_base_url": "http://localhost:11434",
                "requires_api_key": False,
            },
        ],
    }


@router.put("/config/llm")
async def update_llm_config(body: LLMConfigUpdate):
    """Update runtime LLM config for the current FastAPI process."""
    if body.provider not in LLMProvider:
        return {
            "status": "error",
            "message": f"Unsupported provider: {body.provider}",
        }

    llm_config_store.update_provider_config(
        provider=body.provider,
        agent_llm_mode=body.agent_llm_mode,
        anthropic_auth_token=body.anthropic_auth_token,
        model=body.model.strip() if body.model is not None else None,
        base_url=body.base_url.strip() if body.base_url is not None else None,
        api_key=body.api_key.strip() if body.api_key is not None else None,
    )
    updated_model, updated_base_url, updated_api_key = _provider_values(body.provider)
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "agent_llm_mode": settings.AGENT_LLM_MODE,
        "model": updated_model,
        "base_url": updated_base_url,
        "api_key_set": bool(updated_api_key),
        "api_key_preview": _mask_secret(updated_api_key),
    }
