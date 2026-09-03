from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.governance import (
    ControlEvidenceItem,
    ControlInstance,
    EvidenceItem,
    GateSubmission,
    GovernanceAuditLog,
    Project,
    QuestionInstance,
    QuestionnaireInstance,
    RequirementRow,
)


def ok(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "meta": meta or {}, "errors": []}


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def get_project_or_404(
    project_id: uuid.UUID,
    session: Session,
    current_user: Any | None = None,
) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if current_user is not None and project.tenant_id != getattr(
        current_user, "tenant_id", "default"
    ):
        # Do not reveal whether a project exists in another tenant.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def write_audit_event(
    session: Session,
    *,
    actor: Any,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    outcome: str = "success",
    request_id: str | None = None,
    ip_address: str | None = None,
) -> GovernanceAuditLog:
    """Append a tamper-evident audit event inside the caller's transaction."""

    tenant_id = getattr(actor, "tenant_id", "default")
    previous = session.exec(
        select(GovernanceAuditLog)
        .where(GovernanceAuditLog.tenant_id == tenant_id)
        .order_by(GovernanceAuditLog.created_at.desc())
        .with_for_update()
    ).first()
    created_at = datetime.now(UTC)
    payload = {
        "tenant_id": tenant_id,
        "user_id": getattr(actor, "id", None),
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "outcome": outcome,
        "request_id": request_id,
        "ip_address": ip_address,
        "created_at": created_at,
        "previous_hash": previous.event_hash if previous else None,
    }
    event_hash = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    event = GovernanceAuditLog(
        **payload,
        event_hash=event_hash,
    )
    session.add(event)
    return event


def serialize_project(project: Project) -> dict[str, Any]:
    return {
        "id": str(project.id),
        "tenant_id": project.tenant_id,
        "name": project.name,
        "description": project.description,
        "business_owner": project.business_owner,
        "owner_id": project.owner_id,
        "risk_tier": project.risk_tier,
        "control_profile": project.control_profile,
        "compliance_frameworks": project.compliance_frameworks or [],
        "review_mode": project.review_mode,
        "framework_ids_locked": project.framework_ids_locked,
        "involves_ai_ml": project.involves_ai_ml,
        "ai_risk_class": project.ai_risk_class,
        "slsa_target_level": project.slsa_target_level,
        "status": project.status,
        "system_type": project.system_type,
        "hosting_type": project.hosting_type,
        "data_classification": project.data_classification,
        "risk_level": project.risk_level,
        "organization": project.organization,
        "created_at": iso(project.created_at),
        "updated_at": iso(project.updated_at),
    }


def serialize_control(
    control: ControlInstance, evidence_count: int = 0
) -> dict[str, Any]:
    return {
        "id": str(control.id),
        "project_id": str(control.project_id),
        "control_id": control.control_id,
        "framework_id": control.framework_id,
        "framework_citation": control.framework_citation,
        "title": control.title,
        "normalized_requirement": control.normalized_requirement,
        "expected_evidence": control.expected_evidence or [],
        "review_focus": control.review_focus or [],
        "is_applicable": control.is_applicable,
        "applicability_rationale": control.applicability_rationale,
        "is_mandatory": control.is_mandatory,
        "review_mode": control.review_mode,
        "status": control.status,
        "ai_score": control.ai_score,
        "ai_rationale": control.ai_rationale,
        "ai_missing_evidence": control.ai_missing_evidence or [],
        "ai_confidence": control.ai_confidence,
        "ai_requires_human": control.ai_requires_human,
        "human_decision": control.human_decision,
        "human_notes": control.human_notes,
        "evidence_count": evidence_count,
        "created_at": iso(control.created_at),
        "updated_at": iso(control.updated_at),
    }


def serialize_control_evidence(item: ControlEvidenceItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "control_instance_id": str(item.control_instance_id),
        "evidence_type": item.evidence_type,
        "content": item.content,
        "file_path": item.file_path,
        "url": item.url,
        "ai_analysis": item.ai_analysis or {},
        "submitted_at": iso(item.submitted_at),
    }


def serialize_gate_submission(
    submission: GateSubmission,
    rows: list[RequirementRow] | None = None,
    evidence_by_row: dict[uuid.UUID, list[EvidenceItem]] | None = None,
) -> dict[str, Any]:
    return {
        "id": str(submission.id),
        "project_id": str(submission.project_id),
        "gate_number": submission.gate_number,
        "status": submission.status,
        "submitted_at": iso(submission.submitted_at),
        "reviewed_at": iso(submission.reviewed_at),
        "reviewed_by_id": submission.reviewed_by_id,
        "intake_payload": submission.intake_payload or {},
        "reviewer_comments": submission.reviewer_comments,
        "requirements": [
            serialize_requirement_row(row, evidence_by_row.get(row.id, []))
            for row in (rows or [])
            if row.id is not None
        ],
        "created_at": iso(submission.created_at),
        "updated_at": iso(submission.updated_at),
    }


def serialize_requirement_row(
    row: RequirementRow,
    evidence_items: list[EvidenceItem] | None = None,
) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "gate_submission_id": str(row.gate_submission_id),
        "requirement_id": row.requirement_id,
        "domain": row.domain,
        "requirement_text": row.requirement_text,
        "organization_guidance": row.organization_guidance,
        "applicability": row.applicability,
        "risk_level": row.risk_level,
        "review_status": row.review_status,
        "ai_confidence": row.ai_confidence,
        "reviewer_notes": row.reviewer_notes,
        "review_history": row.review_history or [],
        "scd_extras": row.scd_extras or {},
        "evidence_items": [
            serialize_requirement_evidence(item) for item in (evidence_items or [])
        ],
        "created_at": iso(row.created_at),
        "updated_at": iso(row.updated_at),
    }


def serialize_requirement_evidence(item: EvidenceItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "requirement_row_id": str(item.requirement_row_id),
        "evidence_type": item.evidence_type,
        "content": item.content,
        "file_path": item.file_path,
        "url": item.url,
        "ai_analysis": item.ai_analysis or {},
        "submitted_at": iso(item.submitted_at),
    }


def serialize_questionnaire(
    questionnaire: QuestionnaireInstance,
    questions: list[QuestionInstance],
) -> dict[str, Any]:
    return {
        "id": str(questionnaire.id),
        "project_id": str(questionnaire.project_id),
        "generated_from_frameworks": questionnaire.generated_from_frameworks or [],
        "generated_at": iso(questionnaire.generated_at),
        "is_complete": questionnaire.is_complete,
        "completed_at": iso(questionnaire.completed_at),
        "questions": [
            {
                "id": str(question.id),
                "question_key": question.question_key,
                "question_label": question.question_label,
                "question_type": question.question_type,
                "options": question.options or [],
                "group": question.group,
                "ask_when": question.ask_when,
                "sort_order": question.sort_order,
                "maps_to_control_ids": question.maps_to_control_ids or [],
                "answer": question.answer,
                "answered_at": iso(question.answered_at),
            }
            for question in questions
        ],
    }


def evidence_count_by_control(
    controls: list[ControlInstance],
    session: Session,
) -> dict[uuid.UUID, int]:
    counts: dict[uuid.UUID, int] = {}
    for control in controls:
        if control.id is None:
            continue
        counts[control.id] = len(
            session.exec(
                select(ControlEvidenceItem).where(
                    ControlEvidenceItem.control_instance_id == control.id
                )
            ).all()
        )
    return counts
