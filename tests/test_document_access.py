import os

import pytest

from app.core.config import settings
from app.core.document_access import (
    DocumentAccessError,
    resolve_document_path,
    resolve_kb_reindex_directory,
)


def test_resolve_document_path_rejects_path_outside_configured_root(
    monkeypatch, tmp_path
):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("token=secret", encoding="utf-8")
    monkeypatch.setattr(settings, "MCP_DOCUMENT_ROOTS", str(allowed_root))

    with pytest.raises(DocumentAccessError, match="Access denied"):
        resolve_document_path(str(outside_file))


def test_resolve_document_path_allows_path_inside_configured_root(
    monkeypatch, tmp_path
):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    document = allowed_root / "policy.txt"
    document.write_text("Require MFA for admin access.", encoding="utf-8")
    monkeypatch.setattr(settings, "MCP_DOCUMENT_ROOTS", str(allowed_root))

    assert resolve_document_path(str(document)) == document.resolve()


def test_resolve_document_path_rejects_unsupported_extension_before_read(
    monkeypatch, tmp_path
):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    document = allowed_root / "secret.env"
    document.write_text("TOKEN=secret", encoding="utf-8")
    monkeypatch.setattr(settings, "MCP_DOCUMENT_ROOTS", str(allowed_root))

    with pytest.raises(DocumentAccessError, match="Unsupported file type"):
        resolve_document_path(str(document))


def test_resolve_document_path_rejects_symlink_escape(monkeypatch, tmp_path):
    if not hasattr(os, "symlink"):
        pytest.skip("symlink is unavailable on this platform")

    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("token=secret", encoding="utf-8")
    link = allowed_root / "linked-secret.txt"
    try:
        link.symlink_to(outside_file)
    except OSError as exc:
        pytest.skip(f"symlink creation failed: {exc}")

    monkeypatch.setattr(settings, "MCP_DOCUMENT_ROOTS", str(allowed_root))

    with pytest.raises(DocumentAccessError, match="Access denied"):
        resolve_document_path(str(link))


def test_resolve_kb_reindex_directory_rejects_outside_root(monkeypatch, tmp_path):
    allowed_root = tmp_path / "approved"
    allowed_root.mkdir()
    outside_root = tmp_path / "outside"
    outside_root.mkdir()
    monkeypatch.setattr(settings, "KB_REINDEX_ROOTS", str(allowed_root))

    with pytest.raises(DocumentAccessError, match="KB_REINDEX_ROOTS"):
        resolve_kb_reindex_directory(outside_root)


def test_resolve_kb_reindex_directory_allows_approved_root(monkeypatch, tmp_path):
    allowed_root = tmp_path / "approved"
    allowed_root.mkdir()
    monkeypatch.setattr(settings, "KB_REINDEX_ROOTS", str(allowed_root))

    assert resolve_kb_reindex_directory(allowed_root) == allowed_root.resolve()
