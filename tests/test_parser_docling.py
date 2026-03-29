"""Tests for Docling-enhanced parser."""

from unittest.mock import MagicMock, patch

import pytest

from app.parser import parse_file
from app.parser.service import ALLOWED_EXTENSIONS


def test_txt_always_uses_legacy():
    """Plain text files skip Docling regardless of PARSER_ENGINE."""
    with patch("app.parser.service.settings") as mock_settings:
        mock_settings.PARSER_ENGINE = "auto"
        doc = parse_file(b"Hello world", "readme.txt")
        assert doc.metadata.parser_engine == "legacy"
        assert doc.metadata.type == "txt"
        assert doc.content == "Hello world"


def test_md_always_uses_legacy():
    """Markdown files skip Docling regardless of PARSER_ENGINE."""
    with patch("app.parser.service.settings") as mock_settings:
        mock_settings.PARSER_ENGINE = "docling"
        doc = parse_file(b"# Heading\n\nBody", "policy.md")
        assert doc.metadata.parser_engine == "legacy"
        assert doc.metadata.type == "md"


def test_legacy_engine_skips_docling():
    """When PARSER_ENGINE=legacy, Docling is never called."""
    with patch("app.parser.service.settings") as mock_settings:
        mock_settings.PARSER_ENGINE = "legacy"
        with patch("app.parser.service._parse_with_docling") as mock_docling:
            doc = parse_file(b"Simple text content.", "sample.txt")
            mock_docling.assert_not_called()
            assert doc.metadata.parser_engine == "legacy"


def test_auto_engine_falls_back_on_docling_failure():
    """When PARSER_ENGINE=auto and Docling fails, legacy parser is used."""
    from app.parser.service import _LEGACY_PARSERS

    mock_pdf = MagicMock(
        return_value=MagicMock(
            content="fallback",
            metadata=MagicMock(parser_engine="legacy"),
        )
    )
    original = _LEGACY_PARSERS[".pdf"]
    _LEGACY_PARSERS[".pdf"] = mock_pdf
    try:
        with patch("app.parser.service.settings") as mock_settings:
            mock_settings.PARSER_ENGINE = "auto"
            with patch(
                "app.parser.service._parse_with_docling",
                side_effect=RuntimeError("Docling unavailable"),
            ):
                parse_file(b"%PDF-1.4 fake", "report.pdf")
                mock_pdf.assert_called_once()
    finally:
        _LEGACY_PARSERS[".pdf"] = original


def test_docling_engine_raises_on_failure():
    """When PARSER_ENGINE=docling, failure raises (no fallback)."""
    with patch("app.parser.service.settings") as mock_settings:
        mock_settings.PARSER_ENGINE = "docling"
        with patch(
            "app.parser.service._parse_with_docling",
            side_effect=RuntimeError("Docling crash"),
        ):
            with pytest.raises(RuntimeError, match="Docling crash"):
                parse_file(b"%PDF fake", "report.pdf")


def test_auto_engine_calls_docling_for_pdf():
    """When PARSER_ENGINE=auto, Docling is attempted for PDF files."""
    with patch("app.parser.service.settings") as mock_settings:
        mock_settings.PARSER_ENGINE = "auto"
        mock_result = MagicMock(
            content="# Converted\nTable data",
            metadata=MagicMock(parser_engine="docling", type="pdf"),
        )
        with patch(
            "app.parser.service._parse_with_docling", return_value=mock_result
        ) as mock_docling:
            parse_file(b"%PDF-1.4 data", "report.pdf")
            mock_docling.assert_called_once()


def test_allowed_extensions_unchanged():
    """ALLOWED_EXTENSIONS still includes all expected types."""
    expected = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md"}
    assert ALLOWED_EXTENSIONS == expected


def test_unsupported_extension_still_raises():
    """Unsupported file type raises ValueError regardless of engine."""
    with pytest.raises(ValueError, match="Unsupported"):
        parse_file(b"content", "file.xyz")
