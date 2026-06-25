"""Tests for health and root endpoints."""


def test_health_ok(client):
    """GET /health returns status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_root_returns_service_info(client):
    """GET / returns service name and doc links."""
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("service") == "DocSentinel"
    assert data["console"] == "/console"
    assert "api_docs" in data
    assert "health" in data


def test_api_documentation_routes(client):
    assert client.get("/api-docs").status_code == 200
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"] == "DocSentinel API"


def test_config_llm(client):
    """GET /config/llm returns sanitised LLM config."""
    r = client.get("/config/llm")
    assert r.status_code == 200
    data = r.json()
    assert "provider" in data
    assert data["provider"] in {
        "openai",
        "anthropic",
        "qwen",
        "deepseek",
        "openai_compatible",
        "local_openai",
        "ollama",
    }
    assert "model" in data
    assert "providers" in data
    assert any(p["id"] == "local_openai" for p in data["providers"])


def test_update_config_llm_masks_api_key(client):
    """PUT /config/llm updates runtime config and masks API keys."""
    r = client.put(
        "/config/llm",
        json={
            "provider": "openai_compatible",
            "model": "my-model",
            "base_url": "http://localhost:9999/v1",
            "api_key": "sk-test-1234567890",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["provider"] == "openai_compatible"
    assert data["model"] == "my-model"
    assert data["base_url"] == "http://localhost:9999/v1"
    assert data["api_key_set"] is True
    assert data["api_key_preview"] == "sk-t...7890"

    r2 = client.get("/config/llm")
    data2 = r2.json()
    assert data2["api_key_preview"] == "sk-t...7890"
    assert "sk-test-1234567890" not in r2.text
