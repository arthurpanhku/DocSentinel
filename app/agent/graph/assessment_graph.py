from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.models.assessment import AssessmentReport
from app.models.governance import ControlEvidenceItem, ControlInstance
from app.models.parser import ParsedDocument

from .state_types import AssessmentGraphState

logger = logging.getLogger(__name__)


def _session_factory() -> Session:
    return Session(engine)


def _control_id(value: str | None, fallback: str) -> str:
    cleaned = (value or fallback).strip() or fallback
    return cleaned[:64]


def persist_assessment_control_evidence(
    report: AssessmentReport,
    project_id: str | None,
    *,
    session_factory: Callable[[], Session] | None = None,
) -> int:
    """Persist assessment findings as Gate 3 control evidence when project_id exists."""
    if not project_id:
        return 0
    try:
        project_uuid = UUID(str(project_id))
    except ValueError:
        logger.info("Skipping control evidence persistence for non-UUID project_id")
        return 0

    findings = []
    for gap in report.compliance_gaps:
        if gap.id.startswith("S2O-"):
            continue
        findings.append(
            {
                "control_id": _control_id(gap.control_or_clause, gap.id),
                "framework_id": gap.framework or settings.POLICY_PACK_ID,
                "title": gap.control_or_clause,
                "requirement": gap.gap_description,
                "expected_evidence": [gap.evidence_suggestion]
                if gap.evidence_suggestion
                else [],
                "confidence": gap.confidence,
                "kind": "compliance_gap",
            }
        )
    for risk in report.risk_items:
        if risk.category == "rule_engine" or risk.id.startswith("S2O-"):
            continue
        findings.append(
            {
                "control_id": _control_id(risk.category, risk.id),
                "framework_id": settings.POLICY_PACK_ID,
                "title": risk.title,
                "requirement": risk.description or risk.title,
                "expected_evidence": [risk.source_ref] if risk.source_ref else [],
                "confidence": risk.confidence,
                "kind": "risk_item",
            }
        )

    if not findings:
        return 0

    created = 0
    factory = session_factory or _session_factory
    with factory() as session:
        for finding in findings:
            control = ControlInstance(
                project_id=project_uuid,
                control_id=finding["control_id"],
                framework_id=finding["framework_id"],
                title=finding["title"],
                normalized_requirement=finding["requirement"],
                expected_evidence=finding["expected_evidence"],
                review_focus=["gate3", finding["kind"]],
                status="evidence_submitted",
                ai_score=str(finding["confidence"])
                if finding["confidence"] is not None
                else None,
                ai_rationale=report.summary,
                ai_confidence=finding["confidence"],
                ai_requires_human=True,
            )
            session.add(control)
            session.flush()
            session.add(
                ControlEvidenceItem(
                    control_instance_id=control.id,
                    evidence_type="text",
                    content=report.summary,
                    ai_analysis={
                        "task_id": report.task_id,
                        "phase": report.phase,
                        "confidence": report.confidence,
                    },
                )
            )
            created += 1
        session.commit()
    return created


async def _load_skill(state: AssessmentGraphState) -> AssessmentGraphState:
    from app.agent import orchestrator as legacy

    skill_service = legacy.get_skill_service()
    skill_id = state.get("skill_id")
    skill = skill_service.get_skill(skill_id) if skill_id else None
    if not skill:
        logger.warning("No skill_id provided or skill not found; using default skill.")
        skill = skill_service.list_skills()[0]
    return {"skill": skill}


async def _build_context(state: AssessmentGraphState) -> AssessmentGraphState:
    from app.agent import orchestrator as legacy

    skill = state["skill"]
    return {
        "doc_context": legacy._build_document_context(
            state["parsed_documents"],
            skill_focus=skill.risk_focus,
        )
    }


async def _gather_context(state: AssessmentGraphState) -> AssessmentGraphState:
    from app.agent import orchestrator as legacy

    skill = state["skill"]
    doc_context = state["doc_context"]
    policy_future = legacy._policy_and_history_agent(
        doc_context["query_seed"],
        skill_focus=skill.risk_focus,
    )
    evidence_future = legacy._evidence_agent(
        state["parsed_documents"],
        skill.risk_focus,
    )
    (policy_chunks, history_chunks), evidence_context = await asyncio.gather(
        policy_future,
        evidence_future,
    )
    return {
        "policy_chunks": policy_chunks,
        "history_chunks": history_chunks,
        "evidence_context": evidence_context,
    }


async def _draft(state: AssessmentGraphState) -> AssessmentGraphState:
    from app.agent import orchestrator as legacy

    skill = state["skill"]
    full_text = state["doc_context"]["full_text"]
    if len(full_text) > legacy._LARGE_DOC_THRESHOLD:
        draft_raw = await legacy._draft_large_document(
            full_text,
            state["policy_chunks"],
            state["history_chunks"],
            skill=skill,
        )
    else:
        draft_raw = await legacy._drafter_agent(
            full_text,
            state["policy_chunks"],
            state["history_chunks"],
            skill=skill,
        )
    return {"draft_raw": draft_raw}


async def _review(state: AssessmentGraphState) -> AssessmentGraphState:
    from app.agent import orchestrator as legacy

    reviewed_raw = await legacy._reviewer_agent(
        state["draft_raw"],
        state["evidence_context"],
        state["policy_chunks"],
        state["history_chunks"],
        skill=state["skill"],
    )
    return {"reviewed_raw": reviewed_raw}


async def _parse_report(state: AssessmentGraphState) -> AssessmentGraphState:
    from app.agent import orchestrator as legacy

    chunk_lookup = legacy._build_chunk_lookup(
        state["policy_chunks"],
        state["history_chunks"],
    )
    report = legacy._parse_llm_output_to_report(
        raw=state["reviewed_raw"],
        task_id=state["task_id"],
        policy_chunks=state["policy_chunks"],
        history_chunks=state["history_chunks"],
        scenario_id=state.get("scenario_id"),
        project_id=state.get("project_id"),
        phase=state.get("phase"),
        skill_id=state.get("skill_id"),
        chunk_lookup=chunk_lookup,
    )
    return {"report": report}


async def _verify_threat_evidence(
    state: AssessmentGraphState,
) -> AssessmentGraphState:
    from app.services.evidence_critic import verify_threat_model_evidence

    report = await verify_threat_model_evidence(
        state["report"],
        state["parsed_documents"],
    )
    return {"report": report}


async def _persist_governance(state: AssessmentGraphState) -> AssessmentGraphState:
    try:
        count = persist_assessment_control_evidence(
            state["report"],
            state.get("project_id"),
        )
    except Exception as exc:
        logger.warning("control evidence persistence failed: %s", exc)
        count = 0
    return {"persisted_controls": count}


def compile_assessment_graph():
    graph = StateGraph(AssessmentGraphState)
    graph.add_node("load_skill", _load_skill)
    graph.add_node("build_document_context", _build_context)
    graph.add_node("gather_policy_history_and_evidence", _gather_context)
    graph.add_node("draft_assessment", _draft)
    graph.add_node("review_assessment", _review)
    graph.add_node("parse_report", _parse_report)
    graph.add_node("verify_threat_evidence", _verify_threat_evidence)
    graph.add_node("persist_gate3_control_evidence", _persist_governance)
    graph.add_edge(START, "load_skill")
    graph.add_edge("load_skill", "build_document_context")
    graph.add_edge("build_document_context", "gather_policy_history_and_evidence")
    graph.add_edge("gather_policy_history_and_evidence", "draft_assessment")
    graph.add_edge("draft_assessment", "review_assessment")
    graph.add_edge("review_assessment", "parse_report")
    graph.add_edge("parse_report", "verify_threat_evidence")
    graph.add_edge("verify_threat_evidence", "persist_gate3_control_evidence")
    graph.add_edge("persist_gate3_control_evidence", END)
    return graph.compile()


async def run_assessment_graph(
    *,
    task_id,
    parsed_documents: list[ParsedDocument],
    scenario_id: str | None = None,
    project_id: str | None = None,
    phase: str | None = None,
    skill_id: str | None = None,
) -> AssessmentReport:
    compiled = compile_assessment_graph()
    final_state = await compiled.ainvoke(
        {
            "task_id": task_id,
            "parsed_documents": parsed_documents,
            "scenario_id": scenario_id,
            "project_id": project_id,
            "phase": phase,
            "skill_id": skill_id,
        }
    )
    return final_state["report"]
