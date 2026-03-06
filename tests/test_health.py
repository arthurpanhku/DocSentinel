"""Tests for health and root endpoints."""
import pytest


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
    assert data.get("service") == "Arthor Agent"
    assert "docs" in data
    assert "health" in data


def test_config_llm(client):
    """GET /config/llm returns sanitised LLM config."""
    r = client.get("/config/llm")
    assert r.status_code == 200
    data = r.json()
    assert "provider" in data
    assert data["provider"] in ("ollama", "openai")
    assert "model" in data
