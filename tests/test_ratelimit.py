from app.core.config import settings


class _FakeKB:
    async def query(self, query: str, top_k: int):
        return []


def test_llm_endpoint_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "LLM_RATE_LIMIT_REQUESTS_PER_MINUTE", 1)
    monkeypatch.setattr(settings, "LLM_RATE_LIMIT_BURST", 1)
    monkeypatch.setattr("app.api.kb.get_kb_service", lambda: _FakeKB())

    first = client.post("/api/v1/kb/query", json={"query": "mfa", "top_k": 1})
    second = client.post("/api/v1/kb/query", json={"query": "mfa", "top_k": 1})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded"
