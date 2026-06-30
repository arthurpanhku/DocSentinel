"""Runtime LLM configuration persistence for DocSentinel."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

MASKED_SECRET = "***"

PROVIDER_FIELDS: dict[str, tuple[str, str, str | None]] = {
    "openai": ("OPENAI_MODEL", "OPENAI_BASE_URL", "OPENAI_API_KEY"),
    "anthropic": ("ANTHROPIC_MODEL", "ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY"),
    "qwen": ("QWEN_MODEL", "QWEN_BASE_URL", "QWEN_API_KEY"),
    "deepseek": ("DEEPSEEK_MODEL", "DEEPSEEK_BASE_URL", "DEEPSEEK_API_KEY"),
    "openai_compatible": ("COMPAT_MODEL", "COMPAT_BASE_URL", "COMPAT_API_KEY"),
    "local_openai": ("LOCAL_MODEL", "LOCAL_BASE_URL", "LOCAL_API_KEY"),
    "ollama": ("OLLAMA_MODEL", "OLLAMA_BASE_URL", None),
}

PERSISTED_KEYS = {
    "LLM_PROVIDER",
    "AGENT_LLM_MODE",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "QWEN_API_KEY",
    "QWEN_BASE_URL",
    "QWEN_MODEL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "COMPAT_API_KEY",
    "COMPAT_BASE_URL",
    "COMPAT_MODEL",
    "LOCAL_API_KEY",
    "LOCAL_BASE_URL",
    "LOCAL_MODEL",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
}


def _config_path() -> Path:
    return Path(settings.LLM_CONFIG_FILE).expanduser()


def _load_file() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("llm_config_load_failed: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def _save_file(data: dict[str, Any]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    except Exception as exc:
        logger.warning("llm_config_save_failed: %s", exc)


def load_and_apply() -> None:
    """Apply persisted LLM settings to the process-local settings object."""
    stored = _load_file()
    if not stored:
        return

    applied = False
    for key in PERSISTED_KEYS:
        if key not in stored:
            continue
        value = stored[key]
        if value == MASKED_SECRET or not hasattr(settings, key):
            continue
        setattr(settings, key, value)
        applied = True

    if applied:
        from app.llm.base import get_llm

        get_llm.cache_clear()
        logger.info("llm_config_loaded")


def provider_values(provider: str) -> tuple[str, str, str]:
    fields = PROVIDER_FIELDS.get(provider)
    if not fields:
        return "", "", ""
    model_key, base_url_key, api_key_key = fields
    model = str(getattr(settings, model_key, "") or "")
    base_url = str(getattr(settings, base_url_key, "") or "")
    api_key = str(getattr(settings, api_key_key, "") or "") if api_key_key else ""
    return model, base_url, api_key


def update_provider_config(
    *,
    provider: str,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    agent_llm_mode: str | None = None,
    anthropic_auth_token: str | None = None,
) -> None:
    """Persist and apply runtime LLM settings for one DocSentinel provider."""
    if provider not in PROVIDER_FIELDS:
        raise ValueError(f"Unsupported provider: {provider}")

    stored = _load_file()
    settings.LLM_PROVIDER = provider
    stored["LLM_PROVIDER"] = provider

    if agent_llm_mode is not None:
        clean_mode = agent_llm_mode.strip()
        settings.AGENT_LLM_MODE = clean_mode
        stored["AGENT_LLM_MODE"] = clean_mode

    if anthropic_auth_token is not None and anthropic_auth_token != MASKED_SECRET:
        token = anthropic_auth_token.strip()
        settings.ANTHROPIC_AUTH_TOKEN = token
        stored["ANTHROPIC_AUTH_TOKEN"] = token

    model_key, base_url_key, api_key_key = PROVIDER_FIELDS[provider]
    if model is not None:
        clean_model = model.strip()
        setattr(settings, model_key, clean_model)
        stored[model_key] = clean_model
    if base_url is not None:
        clean_base_url = base_url.strip()
        setattr(settings, base_url_key, clean_base_url)
        stored[base_url_key] = clean_base_url
    if api_key_key and api_key is not None and api_key != MASKED_SECRET:
        clean_api_key = api_key.strip()
        setattr(settings, api_key_key, clean_api_key)
        stored[api_key_key] = clean_api_key

    _save_file({key: value for key, value in stored.items() if key in PERSISTED_KEYS})

    from app.llm.base import get_llm

    get_llm.cache_clear()


def current_config() -> dict[str, Any]:
    model, base_url, api_key = provider_values(settings.LLM_PROVIDER)
    return {
        "provider": settings.LLM_PROVIDER,
        "agent_llm_mode": settings.AGENT_LLM_MODE,
        "model": model,
        "base_url": base_url,
        "api_key_set": bool(api_key),
        "anthropic_auth_token_set": bool(settings.ANTHROPIC_AUTH_TOKEN),
    }
