"""
Agent orchestration: multi-agent flow with citations, confidence, and history reuse.
"""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from uuid import UUID

from app.agent.skills_service import get_skill_service
from app.core.config import settings
from app.kb.service import get_kb_service
from app.llm.base import invoke_llm
from app.models.assessment import (
    AssessmentReport,
    ComplianceGap,
    Remediation,
    ReportMetadata,
    RiskItem,
    SourceCitation,
)
from app.models.parser import ParsedDocument

logger = logging.getLogger(__name__)

# Documents longer than this threshold are split for map-reduce assessment.
_LARGE_DOC_THRESHOLD = 12_000
_DOC_CHUNK_SIZE = 10_000
_DOC_CHUNK_OVERLAP = 500


def _truncate_at_boundary(text: str, max_chars: int) -> str:
    """Truncate text at the nearest paragraph or sentence boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    for sep in ["\n\n", "\n", "。", ". ", "；", "; "]:
        pos = truncated.rfind(sep)
        if pos > max_chars * 0.6:
            return truncated[: pos + len(sep)]
    return truncated


def _extract_query_seed(
    full_text: str,
    skill_focus: list[str] | None = None,
    max_chars: int = 2000,
) -> str:
    """Select the most security-relevant paragraphs as a KB query seed.

    Scores each paragraph by occurrence count of skill focus terms, then
    greedily packs the highest-scoring paragraphs up to max_chars.  Falls
    back to the document head when no focus terms are provided.
    """
    if len(full_text) <= max_chars:
        return full_text

    focus_terms = {
        t.lower() for term in (skill_focus or []) for t in term.split() if len(t) > 2
    }

    if not focus_terms:
        return full_text[:max_chars]

    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    if not paragraphs:
        return full_text[:max_chars]

    scored = sorted(
        paragraphs,
        key=lambda p: sum(1 for t in focus_terms if t in p.lower()),
        reverse=True,
    )

    selected: list[str] = []
    total = 0
    for p in scored:
        cost = len(p) + 2  # account for "\n\n" separator
        if total + cost > max_chars:
            break
        selected.append(p)
        total += cost

    return "\n\n".join(selected) if selected else full_text[:max_chars]


def _split_text_with_overlap(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks, breaking at paragraph boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Prefer to break at a paragraph boundary in the latter half of the window.
        boundary = text.rfind("\n\n", start + chunk_size // 2, end)
        if boundary == -1:
            boundary = text.rfind("\n", start + chunk_size // 2, end)
        if boundary == -1:
            boundary = end
        chunks.append(text[start:boundary])
        start = boundary - overlap
    return chunks


async def run_assessment(
    task_id: UUID,
    parsed_documents: list[ParsedDocument],
    scenario_id: str | None = None,
    project_id: str | None = None,
    phase: str | None = None,
    skill_id: str | None = None,
) -> AssessmentReport:
    skill_service = get_skill_service()
    skill = skill_service.get_skill(skill_id) if skill_id else None
    if not skill:
        logger.warning(
            "No skill_id provided or skill not found; "
            "defaulting to first built-in skill."
        )
        skill = skill_service.list_skills()[0]

    doc_context = _build_document_context(
        parsed_documents, skill_focus=skill.risk_focus
    )

    # KB lookup and evidence extraction are independent — run in parallel.
    policy_future = _policy_and_history_agent(
        doc_context["query_seed"],
        skill_focus=skill.risk_focus,
    )
    evidence_future = _evidence_agent(parsed_documents, skill.risk_focus)
    (policy_chunks, history_chunks), evidence_context = await asyncio.gather(
        policy_future,
        evidence_future,
    )

    full_text = doc_context["full_text"]
    if len(full_text) > _LARGE_DOC_THRESHOLD:
        draft_raw = await _draft_large_document(
            full_text,
            policy_chunks,
            history_chunks,
            skill=skill,
        )
    else:
        draft_raw = await _drafter_agent(
            full_text,
            policy_chunks,
            history_chunks,
            skill=skill,
        )

    reviewed_raw = await _reviewer_agent(
        draft_raw,
        evidence_context,
        policy_chunks,
        history_chunks,
        skill=skill,
    )

    chunk_lookup = _build_chunk_lookup(policy_chunks, history_chunks)
    return _parse_llm_output_to_report(
        raw=reviewed_raw,
        task_id=task_id,
        policy_chunks=policy_chunks,
        history_chunks=history_chunks,
        scenario_id=scenario_id,
        project_id=project_id,
        phase=phase,
        skill_id=skill_id,
        chunk_lookup=chunk_lookup,
    )


def _build_document_context(
    parsed_documents: list[ParsedDocument],
    skill_focus: list[str] | None = None,
) -> dict:
    """Combine parsed documents and build a semantically relevant KB query seed."""
    doc_texts: list[str] = []
    for d in parsed_documents:
        c = d.content if isinstance(d.content, str) else str(d.content)
        doc_texts.append(f"[{d.metadata.filename}]\n{c}")
    combined_input = "\n\n---\n\n".join(doc_texts)
    return {
        "full_text": combined_input,
        "query_seed": _extract_query_seed(combined_input, skill_focus),
    }


async def _policy_and_history_agent(
    query_seed: str,
    skill_focus: list[str] | None = None,
) -> tuple[list, list]:
    kb = get_kb_service()

    search_query = query_seed
    if skill_focus:
        focus_terms = " ".join(skill_focus[:3])
        search_query = f"{focus_terms} {query_seed}"

    try:
        policy_chunks = await kb.query(search_query, top_k=5)
    except Exception:
        policy_chunks = []
    try:
        history_chunks = kb.query_history_responses(search_query, top_k=3)
    except Exception:
        history_chunks = []
    return policy_chunks, history_chunks


async def _evidence_agent(
    parsed_documents: list[ParsedDocument],
    skill_focus: list[str] | None = None,
) -> str:
    """Extract security-relevant evidence via LLM, with a keyword-scan fallback."""
    focus_str = ", ".join(skill_focus) if skill_focus else "general security risks"

    doc_parts: list[str] = []
    for d in parsed_documents:
        content = d.content if isinstance(d.content, str) else str(d.content)
        doc_parts.append(
            f"[{d.metadata.filename}]\n{_truncate_at_boundary(content, 6000)}"
        )
    combined = "\n\n---\n\n".join(doc_parts)

    system_prompt = (
        "You are a security evidence extractor. "
        "Extract verbatim lines or short passages that directly support or contradict "
        "the given focus areas. Format each line as: filename#Ln: <exact quote>. "
        "Return only evidence lines, one per line, maximum 30 lines."
    )
    user_prompt = (
        f"Focus areas: {focus_str}\n\n"
        f"Document content:\n{_truncate_at_boundary(combined, 8000)}\n\n"
        "Extract relevant evidence lines:"
    )

    try:
        result = await invoke_llm(system_prompt, user_prompt)
        if result.strip():
            return result.strip()
    except Exception as e:
        logger.warning(
            "LLM evidence extraction failed, falling back to keyword scan: %s", e
        )

    return _evidence_agent_keyword_fallback(parsed_documents, skill_focus)


def _evidence_agent_keyword_fallback(
    parsed_documents: list[ParsedDocument],
    skill_focus: list[str] | None = None,
) -> str:
    """Keyword-based evidence extraction used when LLM extraction is unavailable."""
    evidence_lines: list[str] = []

    keywords = ["password", "encrypt", "access", "token", "risk", "vulnerability"]
    if skill_focus:
        for f in skill_focus:
            keywords.extend(f.lower().split())
    keywords = list(set(keywords))

    for d in parsed_documents:
        content = d.content if isinstance(d.content, str) else str(d.content)
        for i, line in enumerate(content.splitlines()):
            ln = line.strip()
            if not ln:
                continue
            if any(k in ln.lower() for k in keywords):
                evidence_lines.append(f"{d.metadata.filename}#L{i + 1}: {ln[:240]}")
    return (
        "\n".join(evidence_lines[:30])
        or "No explicit security evidence lines extracted."
    )


async def _drafter_agent(
    full_text: str,
    policy_chunks: list,
    history_chunks: list,
    skill: object | None = None,
) -> str:
    policy_context = _format_chunks_with_ids(policy_chunks, prefix="POL")
    history_context = _format_chunks_with_ids(history_chunks, prefix="HIS")

    base_prompt = (
        "You are DrafterAgent in a multi-agent security workflow. "
        "Create an assessment draft in JSON only with keys: summary, risk_items, "
        "compliance_gaps, remediations."
    )

    if skill:
        base_prompt = (
            f"{skill.system_prompt}\n"
            f"You are acting as {skill.name}. {skill.description}\n"
            f"Focus areas: {', '.join(skill.risk_focus)}.\n"
            "Output strictly JSON with keys: summary, risk_items, "
            "compliance_gaps, remediations."
        )

    user_prompt = (
        f"## Documents\n{_truncate_at_boundary(full_text, 12000)}\n\n"
        f"## Policy Chunks\n{_truncate_at_boundary(policy_context, 5000)}\n\n"
        f"## Historical Answers\n{_truncate_at_boundary(history_context, 3000)}\n\n"
        "Generate draft JSON."
    )
    return await invoke_llm(base_prompt, user_prompt)


async def _draft_large_document(
    full_text: str,
    policy_chunks: list,
    history_chunks: list,
    skill: object | None = None,
) -> str:
    """Map-reduce drafting for documents that exceed the single-pass context limit."""
    sections = _split_text_with_overlap(full_text, _DOC_CHUNK_SIZE, _DOC_CHUNK_OVERLAP)
    logger.info(
        "Document exceeds %d chars; running map-reduce over %d sections.",
        _LARGE_DOC_THRESHOLD,
        len(sections),
    )
    section_drafts = await asyncio.gather(
        *[
            _drafter_agent(section, policy_chunks, history_chunks, skill=skill)
            for section in sections
        ]
    )
    return await _merge_drafts(list(section_drafts), skill=skill)


async def _merge_drafts(drafts: list[str], skill: object | None = None) -> str:
    """Consolidate section drafts into one unified assessment JSON."""
    drafts_text = "\n\n---\n\n".join(
        f"## Section {i + 1}\n{d}" for i, d in enumerate(drafts)
    )

    skill_info = ""
    if skill:
        frameworks = ", ".join(getattr(skill, "compliance_frameworks", []))
        skill_info = f"Apply {frameworks} frameworks. "

    system_prompt = (
        "You are MergeAgent. Consolidate multiple security assessment drafts from "
        "different sections of the same document into one unified assessment. "
        f"{skill_info}"
        "Deduplicate findings, keep the highest-severity version of duplicates, "
        "and merge remediations. "
        "Output JSON with keys: summary, risk_items, compliance_gaps, remediations."
    )
    user_prompt = (
        f"{_truncate_at_boundary(drafts_text, 14000)}\n\n"
        "Merge into one unified JSON assessment, deduplicating findings "
        "across sections."
    )
    return await invoke_llm(system_prompt, user_prompt)


async def _reviewer_agent(
    draft_raw: str,
    evidence_context: str,
    policy_chunks: list,
    history_chunks: list,
    skill: object | None = None,
) -> str:
    policy_context = _format_chunks_with_ids(policy_chunks, prefix="POL")
    history_context = _format_chunks_with_ids(history_chunks, prefix="HIS")

    chunk_ids = (
        ", ".join(
            [f"POL-{i + 1}" for i in range(len(policy_chunks))]
            + [f"HIS-{i + 1}" for i in range(len(history_chunks))]
        )
        or "none"
    )

    base_prompt = (
        "You are ReviewerAgent. Validate and improve the draft for consistency and "
        "hallucination resistance. "
        "Output JSON only with keys: summary, confidence, risk_items, "
        "compliance_gaps, remediations, sources. "
        f"Available chunk IDs: {chunk_ids}. "
        "In the `sources` array each entry MUST have: "
        '`"chunk_id"` (one of the available IDs above) and '
        '`"quote"` (verbatim excerpt from that chunk supporting a finding). '
        "Only include chunks you actually used."
    )

    if skill:
        base_prompt = (
            f"You are a Reviewer for the {skill.name} persona. "
            f"Validate the draft against {', '.join(skill.compliance_frameworks)}. "
            "Ensure findings match the persona's focus. "
            "Output JSON only with keys: summary, confidence, risk_items, "
            "compliance_gaps, remediations, sources. "
            f"Available chunk IDs: {chunk_ids}. "
            "In the `sources` array each entry MUST have: "
            '`"chunk_id"` (one of the available IDs above) and '
            '`"quote"` (verbatim excerpt from that chunk supporting a finding). '
            "Only include chunks you actually used."
        )

    user_prompt = (
        f"## Draft\n{_truncate_at_boundary(draft_raw, 8000)}\n\n"
        f"## Evidence Lines\n{_truncate_at_boundary(evidence_context, 2000)}\n\n"
        f"## Policy Chunks\n{_truncate_at_boundary(policy_context, 3000)}\n\n"
        f"## Historical Answers\n{_truncate_at_boundary(history_context, 2000)}\n\n"
        "Keep only well-supported findings. Declare which chunks you used in `sources`."
    )
    return await invoke_llm(base_prompt, user_prompt)


def _format_chunks_with_ids(chunks: list, prefix: str) -> str:
    formatted: list[str] = []
    for i, d in enumerate(chunks):
        metadata = d.metadata or {}
        src = metadata.get("source", "unknown")
        source_type = metadata.get("source_type", "vector")
        c_id = f"{prefix}-{i + 1}"

        if source_type == "graph":
            graph_mode = metadata.get("graph_mode", "hybrid")
            formatted.append(
                f"[{c_id}] [GRAPH/{graph_mode}] {src}\n{d.page_content[:600]}"
            )
        else:
            page = metadata.get("page")
            formatted.append(f"[{c_id}] {src} p={page}\n{d.page_content[:600]}")
    return "\n\n".join(formatted)


def _build_chunk_lookup(
    policy_chunks: list,
    history_chunks: list,
) -> dict[str, object]:
    """Build a chunk_id → Document lookup from the chunks passed to the reviewer."""
    lookup: dict[str, object] = {}
    for i, d in enumerate(policy_chunks):
        lookup[f"POL-{i + 1}"] = d
    for i, d in enumerate(history_chunks):
        lookup[f"HIS-{i + 1}"] = d
    return lookup


def _resolve_citations_from_llm(
    llm_sources: list[dict],
    chunk_lookup: dict[str, object],
) -> list[SourceCitation]:
    """Build SourceCitation objects from the reviewer's declared chunk references."""
    citations: list[SourceCitation] = []
    seen: set[str] = set()

    for i, src in enumerate(llm_sources):
        chunk_id = src.get("chunk_id", "")
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)

        doc = chunk_lookup.get(chunk_id)
        if doc is None:
            continue

        metadata = doc.metadata or {}
        file = metadata.get("source", "unknown")
        page = metadata.get("page")
        paragraph_id = metadata.get("chunk_id") or metadata.get("document_id")
        is_history = chunk_id.startswith("HIS-")

        evidence_link = (
            f"{'history://' if is_history else ''}{file}#chunk={paragraph_id}"
            if paragraph_id
            else None
        )
        citations.append(
            SourceCitation(
                id=f"S{i + 1}",
                file=file,
                page=page if isinstance(page, int) else None,
                paragraph_id=str(paragraph_id) if paragraph_id else None,
                excerpt=src.get("quote", doc.page_content[:240]),
                evidence_link=evidence_link,
                score=float(metadata["score"]) if metadata.get("score") else None,
            )
        )
    return citations


def _derive_sources_from_chunks(
    policy_chunks: list,
    history_chunks: list,
) -> list[SourceCitation]:
    combined = []
    combined.extend([(d, "policy") for d in policy_chunks[:5]])
    combined.extend([(d, "history") for d in history_chunks[:3]])
    citations: list[SourceCitation] = []
    for i, (doc, origin) in enumerate(combined):
        metadata = doc.metadata or {}
        file = metadata.get("source") or "unknown"
        page = metadata.get("page")
        paragraph_id = metadata.get("chunk_id") or metadata.get("document_id")
        citations.append(
            SourceCitation(
                id=f"S{i + 1}",
                file=file,
                page=page if isinstance(page, int) else None,
                paragraph_id=str(paragraph_id) if paragraph_id else None,
                excerpt=doc.page_content[:240],
                evidence_link=f"{file}#chunk={paragraph_id}" if paragraph_id else None,
                score=float(metadata.get("score")) if metadata.get("score") else None,
            )
        )
        if origin == "history" and citations[-1].evidence_link:
            citations[-1].evidence_link = f"history://{citations[-1].evidence_link}"
    return citations


def _parse_llm_output_to_report(
    raw: str,
    task_id: UUID,
    policy_chunks: list,
    history_chunks: list,
    scenario_id: str | None = None,
    project_id: str | None = None,
    phase: str | None = None,
    skill_id: str | None = None,
    chunk_lookup: dict | None = None,
) -> AssessmentReport:
    parsed: dict = {}
    try:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {
            "summary": "Failed to parse LLM output.",
            "risk_items": [],
            "confidence": 0.0,
        }

    # Prefer citations the reviewer explicitly declared; fall back to all passed chunks.
    llm_sources = parsed.get("sources", [])
    if llm_sources and chunk_lookup:
        citations = _resolve_citations_from_llm(llm_sources, chunk_lookup)
    else:
        citations = []

    if not citations:
        citations = _derive_sources_from_chunks(policy_chunks, history_chunks)

    return AssessmentReport(
        task_id=str(task_id),
        phase=phase,
        status="completed",
        summary=parsed.get("summary", "No summary provided."),
        risk_items=[
            RiskItem(
                id=str(uuid.uuid4())[:8],
                title=item.get("title", "Untitled Risk"),
                severity=item.get("severity", "medium"),
                description=item.get("description"),
                source_ref=item.get("source_ref"),
                category=item.get("category"),
            )
            for item in parsed.get("risk_items", [])
        ],
        compliance_gaps=[
            ComplianceGap(
                id=str(uuid.uuid4())[:8],
                control_or_clause=gap.get("control_or_clause", "Unknown"),
                gap_description=gap.get("gap_description", ""),
                evidence_suggestion=gap.get("evidence_suggestion"),
                framework=gap.get("framework"),
            )
            for gap in parsed.get("compliance_gaps", [])
        ],
        remediations=[
            Remediation(
                id=str(uuid.uuid4())[:8],
                action=rem.get("action", "Unknown action"),
                priority=rem.get("priority", "medium"),
                related_risk_ids=rem.get("related_risk_ids", []),
            )
            for rem in parsed.get("remediations", [])
        ],
        confidence=float(parsed.get("confidence", 0.0)),
        sources=citations,
        metadata=ReportMetadata(
            scenario_id=scenario_id,
            project_id=project_id,
            ssdlc_stage=phase,
            ssdlc_phase=phase,
            skill_id=skill_id,
            model_used=settings.LLM_PROVIDER,
            completed_at=datetime.now(UTC),
        ),
    )
