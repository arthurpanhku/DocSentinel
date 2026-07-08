"""Input parsing helpers for evaluation cases."""

from __future__ import annotations

from pathlib import Path

from app.models.parser import ParsedDocument, ParsedDocumentMetadata
from app.parser import parse_file
from app.parser.service import ALLOWED_EXTENSIONS
from evals.models import EvalCase, EvalInput

TEXT_EXTENSIONS = {".java", ".json", ".xml", ".csv", ".yaml", ".yml", ".sarif"}


def parse_inputs(case: EvalCase, input_root: Path) -> list[ParsedDocument]:
    """Parse all inputs for a case into DocSentinel ParsedDocument objects."""
    return [_parse_input(item, input_root) for item in case.inputs]


def _parse_input(item: EvalInput, input_root: Path) -> ParsedDocument:
    path = (input_root / item.path).resolve()
    root = input_root.resolve()
    if not str(path).startswith(str(root)):
        raise ValueError(f"Input path escapes input root: {item.path}")
    if not path.exists():
        raise FileNotFoundError(path)

    suffix = path.suffix.lower()
    content = path.read_bytes()
    if suffix in ALLOWED_EXTENSIONS:
        return parse_file(content, path.name)
    if suffix in TEXT_EXTENSIONS or item.type in {"java", "text", "source"}:
        text = content.decode("utf-8", errors="replace")
        return ParsedDocument(
            content=text,
            metadata=ParsedDocumentMetadata(
                filename=path.name,
                type="txt",
                parser_engine="legacy",
            ),
        )
    raise ValueError(f"Unsupported eval input type: {item.type} ({path.name})")

