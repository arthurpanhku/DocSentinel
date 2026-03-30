"""
Parsed document model.
Aligned with docs/03-assessment-report-and-skill-contract.md §2 Parser Output Schema.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ParsedDocumentMetadata(BaseModel):
    filename: str
    type: Literal["pdf", "docx", "xlsx", "pptx", "txt", "md", "mmd", "mermaid"]
    parser_engine: Literal["docling", "legacy"] = "legacy"
    upload_time: datetime = Field(default_factory=_utcnow)
    scenario_id: str | None = None
    file_hash: str | None = None


class ParsedDocument(BaseModel):
    metadata: ParsedDocumentMetadata
    content: str  # Markdown or text
    raw_structure: dict | None = None  # JSON for spreadsheets/tables
    chunk_ids: list[str] = Field(default_factory=list)
