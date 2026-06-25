import os
from pathlib import Path

from app.core.config import settings
from app.parser.service import ALLOWED_EXTENSIONS


class DocumentAccessError(ValueError):
    """Raised when a document path is outside configured roots."""


def _configured_roots(value: str, default: str) -> list[Path]:
    roots = [item.strip() for item in value.split(os.pathsep) if item.strip()]
    if not roots:
        roots = [default]
    return [Path(root).expanduser().resolve(strict=False) for root in roots]


def document_roots() -> list[Path]:
    return _configured_roots(settings.MCP_DOCUMENT_ROOTS, "./examples")


def kb_reindex_roots() -> list[Path]:
    return _configured_roots(settings.KB_REINDEX_ROOTS, "./examples")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_path(
    raw_path: str | Path,
    roots: list[Path],
    *,
    setting_name: str,
    expect_directory: bool,
) -> Path:
    requested = Path(raw_path).expanduser()
    if not requested.is_absolute():
        requested = Path.cwd() / requested

    preliminary_path = requested.resolve(strict=False)
    if not any(_is_relative_to(preliminary_path, root) for root in roots):
        raise DocumentAccessError(f"Access denied: path must be inside {setting_name}")

    try:
        resolved_path = requested.resolve(strict=True)
    except FileNotFoundError:
        raise FileNotFoundError(f"Path not found: {raw_path}") from None

    if not any(_is_relative_to(resolved_path, root) for root in roots):
        raise DocumentAccessError(
            f"Access denied: resolved path escapes {setting_name}"
        )
    if expect_directory and not resolved_path.is_dir():
        raise DocumentAccessError("Access denied: path must reference a directory")
    if not expect_directory and not resolved_path.is_file():
        raise DocumentAccessError("Access denied: file_path must reference a file")
    return resolved_path


def resolve_document_path(file_path: str) -> Path:
    resolved_path = _resolve_path(
        file_path,
        document_roots(),
        setting_name="MCP_DOCUMENT_ROOTS",
        expect_directory=False,
    )
    if resolved_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise DocumentAccessError(
            f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return resolved_path


def resolve_kb_reindex_directory(directory: str | Path) -> Path:
    return _resolve_path(
        directory,
        kb_reindex_roots(),
        setting_name="KB_REINDEX_ROOTS",
        expect_directory=True,
    )
