"""Health and runtime configuration endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.llm.base import get_llm

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


def _mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _provider_values(provider: str) -> tuple[str, str, str]:
    if provider == "openai":
        return settings.OPENAI_MODEL, settings.OPENAI_BASE_URL, settings.OPENAI_API_KEY
    if provider == "anthropic":
        return (
            settings.ANTHROPIC_MODEL,
            settings.ANTHROPIC_BASE_URL,
            settings.ANTHROPIC_API_KEY,
        )
    if provider == "qwen":
        return settings.QWEN_MODEL, settings.QWEN_BASE_URL, settings.QWEN_API_KEY
    if provider == "deepseek":
        return (
            settings.DEEPSEEK_MODEL,
            settings.DEEPSEEK_BASE_URL,
            settings.DEEPSEEK_API_KEY,
        )
    if provider == "openai_compatible":
        return settings.COMPAT_MODEL, settings.COMPAT_BASE_URL, settings.COMPAT_API_KEY
    if provider == "local_openai":
        return settings.LOCAL_MODEL, settings.LOCAL_BASE_URL, settings.LOCAL_API_KEY
    if provider == "ollama":
        return settings.OLLAMA_MODEL, settings.OLLAMA_BASE_URL, ""
    return "", "", ""


def _set_provider_values(
    provider: str,
    model: str | None,
    base_url: str | None,
    api_key: str | None,
) -> None:
    if provider == "openai":
        if model is not None:
            settings.OPENAI_MODEL = model
        if base_url is not None:
            settings.OPENAI_BASE_URL = base_url
        if api_key is not None:
            settings.OPENAI_API_KEY = api_key
    elif provider == "anthropic":
        if model is not None:
            settings.ANTHROPIC_MODEL = model
        if base_url is not None:
            settings.ANTHROPIC_BASE_URL = base_url
        if api_key is not None:
            settings.ANTHROPIC_API_KEY = api_key
    elif provider == "qwen":
        if model is not None:
            settings.QWEN_MODEL = model
        if base_url is not None:
            settings.QWEN_BASE_URL = base_url
        if api_key is not None:
            settings.QWEN_API_KEY = api_key
    elif provider == "deepseek":
        if model is not None:
            settings.DEEPSEEK_MODEL = model
        if base_url is not None:
            settings.DEEPSEEK_BASE_URL = base_url
        if api_key is not None:
            settings.DEEPSEEK_API_KEY = api_key
    elif provider == "openai_compatible":
        if model is not None:
            settings.COMPAT_MODEL = model
        if base_url is not None:
            settings.COMPAT_BASE_URL = base_url
        if api_key is not None:
            settings.COMPAT_API_KEY = api_key
    elif provider == "local_openai":
        if model is not None:
            settings.LOCAL_MODEL = model
        if base_url is not None:
            settings.LOCAL_BASE_URL = base_url
        if api_key is not None:
            settings.LOCAL_API_KEY = api_key
    elif provider == "ollama":
        if model is not None:
            settings.OLLAMA_MODEL = model
        if base_url is not None:
            settings.OLLAMA_BASE_URL = base_url


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/config/llm")
async def config_llm():
    """Current LLM config with secrets masked."""
    model, base_url, api_key = _provider_values(settings.LLM_PROVIDER)
    return {
        "provider": settings.LLM_PROVIDER,
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

    settings.LLM_PROVIDER = body.provider
    _set_provider_values(
        body.provider,
        body.model.strip() if body.model is not None else None,
        body.base_url.strip() if body.base_url is not None else None,
        body.api_key.strip() if body.api_key is not None else None,
    )
    get_llm.cache_clear()
    updated_model, updated_base_url, updated_api_key = _provider_values(body.provider)
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "model": updated_model,
        "base_url": updated_base_url,
        "api_key_set": bool(updated_api_key),
        "api_key_preview": _mask_secret(updated_api_key),
    }
