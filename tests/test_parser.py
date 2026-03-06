"""Tests for document parser (no LLM)."""
import pytest

from app.parser import parse_file
from app.parser.service import ALLOWED_EXTENSIONS


def test_parse_txt():
    """Parse plain text file."""
    content = b"Hello, this is a security questionnaire.\nAnswer: Yes."
    doc = parse_file(content, "sample.txt")
    assert doc.content is not None
    assert "security questionnaire" in doc.content
    assert doc.metadata.filename == "sample.txt"
    assert doc.format == "markdown"


def test_parse_md():
    """Parse markdown file."""
    content = b"# Policy\n\n- Item 1\n- Item 2"
    doc = parse_file(content, "policy.md")
    assert "Policy" in doc.content
    assert doc.metadata.filename == "policy.md"


def test_parse_unsupported_extension_raises():
    """Unsupported file type raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        parse_file(b"content", "file.xyz")
    assert "Unsupported" in str(exc_info.value)
    assert "Allowed" in str(exc_info.value)


def test_allowed_extensions_include_common():
    """Allowed extensions include expected types."""
    assert ".pdf" in ALLOWED_EXTENSIONS
    assert ".docx" in ALLOWED_EXTENSIONS
    assert ".txt" in ALLOWED_EXTENSIONS
    assert ".md" in ALLOWED_EXTENSIONS
