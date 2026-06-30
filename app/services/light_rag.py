"""Light RAG style local knowledge retrieval for MVP agents."""

from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}")
_ROOT = Path(__file__).resolve().parents[2]


def _knowledge_dirs() -> tuple[Path, ...]:
    from app.services.policy_pack import load_policy_pack

    pack = load_policy_pack()
    return (
        _ROOT / "knowledge_base" / "distilled",
        _ROOT / "knowledge_base" / "uploads" / "distilled",
        pack.root / "schemas",
        pack.root / "knowledge",
    )


@dataclass(frozen=True)
class KnowledgeChunk:
    content: str
    source: str
    section: str
    chunk_id: str
    relevance: float


@dataclass(frozen=True)
class _IndexedChunk:
    content: str
    source: str
    section: str
    chunk_id: str
    tokens: frozenset[str]


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")}


def _iter_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("Document", [])]
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip() or "Untitled"
            sections.append((heading, []))
        else:
            sections[-1][1].append(line)
    return [
        (title, "\n".join(lines).strip())
        for title, lines in sections
        if "\n".join(lines).strip()
    ]


def _chunk_section(body: str, max_chars: int = 1400) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            current = para[:max_chars]
    if current:
        chunks.append(current)
    return chunks


@lru_cache(maxsize=1)
def _build_index() -> tuple[_IndexedChunk, ...]:
    rows: list[_IndexedChunk] = []
    for folder in _knowledge_dirs():
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            try:
                source = str(path.relative_to(_ROOT))
            except ValueError:
                source = str(path)
            for section, body in _iter_sections(text):
                for idx, chunk in enumerate(_chunk_section(body)):
                    seed = f"{source}:{section}:{idx}"
                    rows.append(
                        _IndexedChunk(
                            content=chunk,
                            source=source,
                            section=section,
                            chunk_id=str(uuid.uuid5(uuid.NAMESPACE_URL, seed)),
                            tokens=frozenset(_tokens(f"{section}\n{chunk}")),
                        )
                    )
    return tuple(rows)


def search_knowledge(
    query: str, *, kb_type: str | None = None, gate: str | None = None, top_k: int = 5
) -> list[KnowledgeChunk]:
    """Return relevant local knowledge chunks using a lightweight lexical score."""

    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    scored: list[tuple[float, _IndexedChunk]] = []
    gate_l = (gate or "").lower()
    for row in _build_index():
        if (
            gate_l
            and gate_l not in row.source.lower()
            and gate_l not in row.section.lower()
            and gate_l not in row.content.lower()
        ):
            continue
        overlap = query_tokens & row.tokens
        if not overlap:
            continue
        precision = len(overlap) / max(len(query_tokens), 1)
        coverage = len(overlap) / math.sqrt(max(len(row.tokens), 1))
        score = round((precision * 0.75) + (coverage * 0.25), 4)
        scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        KnowledgeChunk(
            content=row.content,
            source=row.source,
            section=row.section,
            chunk_id=row.chunk_id,
            relevance=score,
        )
        for score, row in scored[: max(1, min(top_k, 10))]
    ]


def format_knowledge_context(chunks: list[KnowledgeChunk]) -> str:
    if not chunks:
        return ""
    parts = ["[KNOWLEDGE CONTEXT]"]
    for idx, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[{idx}] source={chunk.source} section={chunk.section} "
            f"chunk_id={chunk.chunk_id} relevance={chunk.relevance}\n"
            f"{chunk.content}"
        )
    parts.append("[END KNOWLEDGE CONTEXT]")
    return "\n\n".join(parts)


def chunks_to_citations(chunks: list[KnowledgeChunk]) -> list[dict]:
    citations: list[dict] = []
    for idx, chunk in enumerate(chunks):
        citations.append(
            {
                "document_id": str(uuid.UUID(chunk.chunk_id)),
                "chunk_index": idx,
                "source": chunk.source,
                "section": chunk.section,
                "excerpt": chunk.content[:500],
                "score": chunk.relevance,
            }
        )
    return citations
