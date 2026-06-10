import os
from pathlib import Path

from app.core.config import settings
from app.parser.service import ALLOWED_EXTENSIONS


class DocumentAccessError(ValueError):
    """Raised when a document path is outside configured roots."""


def document_roots() -> list[Path]:
    roots = [
        value.strip()
        for value in settings.MCP_DOCUMENT_ROOTS.split(os.pathsep)
        if value.strip()
    ]
    if not roots:
        roots = ["."]
    return [Path(root).expanduser().resolve(strict=False) for root in roots]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_document_path(file_path: str) -> Path:
    requested = Path(file_path).expanduser()
    if not requested.is_absolute():
        requested = Path.cwd() / requested

    roots = document_roots()
    preliminary_path = requested.resolve(strict=False)
    if not any(_is_relative_to(preliminary_path, root) for root in roots):
        raise DocumentAccessError(
            "Access denied: file_path must be inside MCP_DOCUMENT_ROOTS"
        )

    try:
        resolved_path = requested.resolve(strict=True)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}") from None

    if not any(_is_relative_to(resolved_path, root) for root in roots):
        raise DocumentAccessError(
            "Access denied: resolved file_path escapes MCP_DOCUMENT_ROOTS"
        )
    if not resolved_path.is_file():
        raise DocumentAccessError("Access denied: file_path must reference a file")
    if resolved_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise DocumentAccessError(
            f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return resolved_path
