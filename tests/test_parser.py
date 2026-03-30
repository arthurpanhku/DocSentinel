"""Tests for document parser (no LLM)."""

import pytest

from app.parser import parse_file
from app.parser.service import ALLOWED_EXTENSIONS


def test_parse_txt():
    content = b"Simple text content."
    doc = parse_file(content, "sample.txt")
    assert doc.metadata.filename == "sample.txt"
    assert doc.metadata.type == "txt"
    assert doc.content == "Simple text content."


def test_parse_md():
    content = b"# Heading\n\n- item 1"
    doc = parse_file(content, "policy.md")
    assert doc.metadata.filename == "policy.md"
    assert doc.metadata.type == "md"
    assert "# Heading" in doc.content


def test_parse_mermaid_mmd():
    content = b"flowchart TB\n  A-->B"
    doc = parse_file(content, "arch.mmd")
    assert doc.metadata.filename == "arch.mmd"
    assert doc.metadata.type == "mmd"
    assert doc.content.startswith("```mermaid\n")
    assert "flowchart TB" in doc.content
    assert doc.content.endswith("\n```")


def test_parse_mermaid_extension():
    content = b"sequenceDiagram\n  Alice->>Bob: Hi"
    doc = parse_file(content, "seq.mermaid")
    assert doc.metadata.filename == "seq.mermaid"
    assert doc.metadata.type == "mermaid"
    assert "```mermaid" in doc.content


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
    assert ".mmd" in ALLOWED_EXTENSIONS
    assert ".mermaid" in ALLOWED_EXTENSIONS
