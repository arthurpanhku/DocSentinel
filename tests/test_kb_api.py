from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings


def test_reindex_rejects_directory_outside_configured_roots(
    client, monkeypatch, tmp_path
):
    approved = tmp_path / "approved"
    approved.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setattr(settings, "KB_REINDEX_ROOTS", str(approved))

    response = client.post("/api/v1/kb/reindex", json={"directory": str(outside)})

    assert response.status_code == 403
    assert "KB_REINDEX_ROOTS" in response.json()["detail"]


def test_reindex_uses_resolved_approved_directory(client, monkeypatch, tmp_path):
    approved = tmp_path / "approved"
    approved.mkdir()
    monkeypatch.setattr(settings, "KB_REINDEX_ROOTS", str(approved))

    kb = MagicMock()
    kb.reindex_directory = AsyncMock(
        return_value={"directory": str(approved), "indexed": 0, "errors": []}
    )
    with patch("app.api.kb.get_kb_service", return_value=kb):
        response = client.post(
            "/api/v1/kb/reindex",
            json={"directory": str(approved)},
        )

    assert response.status_code == 200
    kb.reindex_directory.assert_awaited_once_with(approved.resolve())
