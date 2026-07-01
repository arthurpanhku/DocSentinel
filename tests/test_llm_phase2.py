"""Phase 2 LLM configuration and safety coverage."""

import json

from app.core.config import settings
from app.core.guardrails import sanitize_text
from app.llm.base import get_llm
from app.services import llm_config_store


def test_get_llm_constructs_deepseek(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_LLM_MODE", "")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "deepseek")
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")
    get_llm.cache_clear()
    try:
        llm = get_llm()
        assert llm.__class__.__name__ == "ChatOpenAI"
    finally:
        get_llm.cache_clear()


def test_get_llm_constructs_anthropic_compat(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_LLM_MODE", "anthropic_compat")
    monkeypatch.setattr(settings, "ANTHROPIC_AUTH_TOKEN", "sk-ant-test")
    monkeypatch.setattr(settings, "ANTHROPIC_BASE_URL", "https://anthropic.example/v1")
    monkeypatch.setattr(settings, "ANTHROPIC_MODEL", "")
    monkeypatch.setattr(settings, "ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-test")
    get_llm.cache_clear()
    try:
        llm = get_llm()
        assert llm.__class__.__name__ == "ChatAnthropic"
    finally:
        get_llm.cache_clear()


def test_sanitize_text_redacts_email_ip_and_phone():
    out = sanitize_text(
        "owner alice@example.com connects from 10.2.3.4 and 13800138000"
    )

    assert "[REDACTED_EMAIL]" in out.text
    assert "[REDACTED_IP]" in out.text
    assert "[REDACTED_PHONE]" in out.text
    assert set(out.redacted_fields) >= {"email", "ipv4", "cn_mobile"}


def test_llm_config_store_persists_and_loads(monkeypatch, tmp_path):
    config_file = tmp_path / "llm_config.json"
    monkeypatch.setattr(settings, "LLM_CONFIG_FILE", str(config_file))
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "AGENT_LLM_MODE", "")
    monkeypatch.setattr(settings, "DEEPSEEK_MODEL", "")
    monkeypatch.setattr(settings, "DEEPSEEK_BASE_URL", "")
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "")

    llm_config_store.update_provider_config(
        provider="deepseek",
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key="sk-test-123",
        agent_llm_mode="",
    )

    stored = json.loads(config_file.read_text(encoding="utf-8"))
    assert stored["LLM_PROVIDER"] == "deepseek"
    assert stored["DEEPSEEK_MODEL"] == "deepseek-chat"
    assert stored["DEEPSEEK_API_KEY"] == "sk-test-123"

    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "DEEPSEEK_MODEL", "")
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "")
    llm_config_store.load_and_apply()

    assert settings.LLM_PROVIDER == "deepseek"
    assert settings.DEEPSEEK_MODEL == "deepseek-chat"
    assert settings.DEEPSEEK_API_KEY == "sk-test-123"
