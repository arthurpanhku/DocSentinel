"""
Agent orchestration: multi-agent flow with citations, confidence, and history reuse.
"""

import uuid
from datetime import datetime
from uuid import UUID

from app.agent.skills_service import get_skill_service
from app.core.config import settings
from app.kb.service import KnowledgeBaseService
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


async def run_assessment(
    task_id: UUID,
    parsed_documents: list[ParsedDocument],
    scenario_id: str | None = None,
    project_id: str | None = None,
    skill_id: str | None = None,
) -> AssessmentReport:
    # 1. Load Skill (Persona)
    skill_service = get_skill_service()
    # Default to first builtin if not provided or found
    skill = skill_service.get_skill(skill_id) if skill_id else None
    if not skill:
        skill = skill_service.list_skills()[0]

    doc_context = _build_document_context(parsed_documents)

    # Pass skill context to agents
    policy_chunks, history_chunks = await _policy_and_history_agent(
        doc_context["query_seed"],
        skill_focus=skill.risk_focus
    )

    evidence_context = _evidence_agent(parsed_documents, skill_focus=skill.risk_focus)

    draft_raw = await _drafter_agent(
        doc_context["full_text"],
        policy_chunks,
        history_chunks,
        skill=skill
    )

    reviewed_raw = await _reviewer_agent(
        draft_raw,
        evidence_context,
        policy_chunks,
        history_chunks,
        skill=skill
    )

    report = await _parse_llm_output_to_report(
        raw=reviewed_raw,
        task_id=task_id,
        policy_chunks=policy_chunks,
        history_chunks=history_chunks,
        scenario_id=scenario_id,
        project_id=project_id,
    )
    return report


def _build_document_context(parsed_documents: list[ParsedDocument]) -> dict:
    """Combine parsed documents into a single text block."""
    doc_texts: list[str] = []
    for d in parsed_documents:
        c = d.content if isinstance(d.content, str) else str(d.content)
        doc_texts.append(f"[{d.metadata.filename}]\n{c}")
    combined_input = "\n\n---\n\n".join(doc_texts)
    return {"full_text": combined_input, "query_seed": combined_input[:2000]}




async def _policy_and_history_agent(
    query_seed: str,
    skill_focus: list[str] | None = None
) -> tuple[list, list]:
    kb = KnowledgeBaseService()

    # Enrich query with skill focus
    search_query = query_seed
    if skill_focus:
        focus_terms = " ".join(skill_focus[:3])
        search_query = f"{focus_terms} {query_seed}"

    policy_chunks = []
    history_chunks = []
    try:
        # Hybrid query: vector + graph RAG (when enabled)
        policy_chunks = await kb.query(search_query, top_k=5)
    except Exception:
        policy_chunks = []
    try:
        history_chunks = kb.query_history_responses(search_query, top_k=3)
    except Exception:
        history_chunks = []
    return policy_chunks, history_chunks


def _evidence_agent(
    parsed_documents: list[ParsedDocument],
    skill_focus: list[str] | None = None
) -> str:
    evidence_lines: list[str] = []

    # Default keywords
    keywords = ["password", "encrypt", "access", "token", "risk", "vulnerability"]
    # Add skill focus keywords
    if skill_focus:
        for f in skill_focus:
            keywords.extend(f.lower().split())

    keywords = list(set(keywords))  # dedupe

    for d in parsed_documents:
        content = d.content if isinstance(d.content, str) else str(d.content)
        for i, line in enumerate(content.splitlines()):
            ln = line.strip()
            if not ln:
                continue
            if any(k in ln.lower() for k in keywords):
                evidence_lines.append(f"{d.metadata.filename}#L{i + 1}: {ln[:240]}")
    return (
        "\n".join(evidence_lines[:30])  # Increased from 20
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

    # Inject Skill Persona
    if skill:
        base_prompt = (
            f"{skill.system_prompt}\n"
            f"You are acting as {skill.name}. {skill.description}\n"
            f"Focus areas: {', '.join(skill.risk_focus)}.\n"
            "Output strictly JSON with keys: summary, risk_items, compliance_gaps, remediations."
        )

    user_prompt = (
        f"## Documents\n{full_text[:12000]}\n\n"
        f"## Policy Chunks\n{policy_context[:5000]}\n\n"
        f"## Historical Answers\n{history_context[:3000]}\n\n"
        "Generate draft JSON."
    )
    return await invoke_llm(base_prompt, user_prompt)


async def _reviewer_agent(
    draft_raw: str,
    evidence_context: str,
    policy_chunks: list,
    history_chunks: list,
    skill: object | None = None,
) -> str:
    policy_context = _format_chunks_with_ids(policy_chunks, prefix="POL")
    history_context = _format_chunks_with_ids(history_chunks, prefix="HIS")

    base_prompt = (
        "You are ReviewerAgent. Validate and improve the draft for consistency and "
        "hallucination resistance. Output JSON only with keys: summary, confidence, "
        "risk_items, compliance_gaps, remediations, sources."
    )

    if skill:
        base_prompt = (
            f"You are a Reviewer for the {skill.name} persona. "
            f"Validate the draft against {', '.join(skill.compliance_frameworks)}. "
            "Ensure findings match the persona's focus. "
            "Output JSON only with keys: summary, confidence, risk_items, "
            "compliance_gaps, remediations, sources."
        )

    user_prompt = (
        f"## Draft\n{draft_raw[:8000]}\n\n"
        f"## Evidence Lines\n{evidence_context[:2000]}\n\n"
        f"## Policy Chunks\n{policy_context[:3000]}\n\n"
        f"## Historical Answers\n{history_context[:2000]}\n\n"
        "Keep only well-supported findings. Add explicit sources and confidence."
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


async def _estimate_confidence(
    summary: str,
    risk_count: int,
    source_count: int,
) -> float:
    system_prompt = (
        "You are ConfidenceAgent. Output only one float between 0 and 1 based on "
        "evidence strength and consistency."
    )
    user_prompt = (
        f"summary={summary[:500]}\n"
        f"risk_count={risk_count}\n"
        f"source_count={source_count}\n"
        "Return float only."
    )
    try:
        raw = await invoke_llm(system_prompt, user_prompt)
        value = float(str(raw).strip().split()[0])
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value
    except Exception:
        heuristic = 0.55 + min(source_count, 5) * 0.06 - min(risk_count, 6) * 0.02
        if heuristic < 0.0:
            return 0.0
        if heuristic > 1.0:
            return 1.0
        return round(heuristic, 2)


async def _parse_llm_output_to_report(
    raw: str,
    task_id: UUID,
    policy_chunks: list,
    history_chunks: list,
    scenario_id: str | None = None,
    project_id: str | None = None,
) -> AssessmentReport:
    import json

    # Attempt to extract JSON
    parsed = {}
    try:
        # Simple cleanup
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback if LLM output isn't clean JSON
        parsed = {
            "summary": "Failed to parse LLM output.",
            "risk_items": [],
            "confidence": 0.0,
        }

    # Construct source citations
    citations = _derive_sources_from_chunks(policy_chunks, history_chunks)

    # Merge LLM-generated sources if any
    llm_sources = parsed.get("sources", [])
    if isinstance(llm_sources, list):
        # We might merge or validate them here. For MVP, we'll append unique ones
        # or just rely on our derived citations which are grounded in truth.
        # Let's trust derived citations more for now.
        pass

    return AssessmentReport(
        task_id=str(task_id),
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
            model_used=settings.LLM_PROVIDER,
            completed_at=datetime.utcnow(),
        ),
    )
