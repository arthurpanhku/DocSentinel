import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.mcp_server import assess_document


@pytest.mark.asyncio
async def test_assess_document_rejects_outside_path_before_parse(monkeypatch, tmp_path):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("token=secret", encoding="utf-8")
    monkeypatch.setattr(settings, "MCP_DOCUMENT_ROOTS", str(allowed_root))

    with (
        patch("app.mcp_server.parse_file") as parse_file,
        patch("app.mcp_server.run_assessment", new_callable=AsyncMock) as run,
    ):
        result = json.loads(await assess_document(str(outside_file)))

    assert "Access denied" in result["error"]
    parse_file.assert_not_called()
    run.assert_not_called()
