from __future__ import annotations

# ruff: noqa: B008
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.security import ensure_role
from app.models.governance import (
    EvidenceItem,
    EvidenceType,
    GateStatus,
    GateSubmission,
    RequirementRow,
    ReviewStatus,
)
from app.models.governance.submission import (
    COMMENT_REQUIRED_TRANSITIONS,
    GATE_STATUS_TRANSITIONS,
)
from app.services.schema_service import get_gate3_controls

from .utils import (
    get_project_or_404,
    ok,
    serialize_gate_submission,
    serialize_requirement_row,
    write_audit_event,
)

router = APIRouter(tags=["governance-submissions"])


class GateSubmissionPayload(BaseModel):
    intake_payload: dict[str, Any] = Field(default_factory=dict)
    requirements: list[dict[str, Any]] = Field(default_factory=list)


class GateReviewPayload(BaseModel):
    status: Literal["approved", "changes_requested", "rejected", "completed"]
    reviewer_comments: str | None = None
    reviewed_by_id: int | None = None  # Deprecated: authenticated actor is used.


class RequirementRowUpdate(BaseModel):
    requirement_text: str | None = None
    organization_guidance: str | None = None
    applicability: str | None = None
    risk_level: str | None = None
    review_status: (
        Literal[
            "pending_review",
            "accepted",
            "rejected",
            "needs_clarification",
        ]
        | None
    ) = None
    reviewer_notes: str | None = None
    scd_extras: dict[str, Any] | None = None


class RequirementEvidenceRequest(BaseModel):
    evidence_type: Literal["text", "image", "link"] = "text"
    content: str | None = None
    file_path: str | None = None
    url: str | None = None


def _rows_for(
    session: Session,
    submission_id: uuid.UUID,
) -> list[RequirementRow]:
    return session.exec(
        select(RequirementRow)
        .where(RequirementRow.gate_submission_id == submission_id)
        .order_by(RequirementRow.created_at)
    ).all()


def _evidence_by_row(
    session: Session,
    rows: list[RequirementRow],
) -> dict[uuid.UUID, list[EvidenceItem]]:
    result: dict[uuid.UUID, list[EvidenceItem]] = {}
    for row in rows:
        if row.id is None:
            continue
        result[row.id] = session.exec(
            select(EvidenceItem).where(EvidenceItem.requirement_row_id == row.id)
        ).all()
    return result


def _project_for_row(
    row: RequirementRow,
    session: Session,
    current_user: Any,
) -> None:
    submission = session.get(GateSubmission, row.gate_submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gate submission not found",
        )
    get_project_or_404(submission.project_id, session, current_user)


def _get_or_create_submission(
    project_id: uuid.UUID,
    gate_number: int,
    session: Session,
) -> GateSubmission:
    submission = session.exec(
        select(GateSubmission).where(
            GateSubmission.project_id == project_id,
            GateSubmission.gate_number == gate_number,
        )
    ).first()
    if submission is None:
        submission = GateSubmission(
            project_id=project_id,
            gate_number=gate_number,
            status=GateStatus.draft.value,
            intake_payload={} if gate_number == 1 else None,
        )
        session.add(submission)
        session.flush()
    return submission


def _seed_gate3_rows(submission: GateSubmission, session: Session) -> None:
    if submission.gate_number != 3 or submission.id is None:
        return
    existing = session.exec(
        select(RequirementRow).where(RequirementRow.gate_submission_id == submission.id)
    ).first()
    if existing is not None:
        return
    for control in get_gate3_controls("full_ssdlc"):
        session.add(
            RequirementRow(
                gate_submission_id=submission.id,
                requirement_id=str(control.get("control_id") or ""),
                domain=str(control.get("family") or "General"),
                requirement_text=str(
                    control.get("normalized_requirement")
                    or control.get("title")
                    or control.get("control_id")
                ),
                organization_guidance=str(control.get("title") or ""),
                applicability="applicable",
                risk_level="medium",
                review_status=ReviewStatus.pending_review.value,
                scd_extras={
                    "expected_evidence": control.get("expected_evidence") or []
                },
            )
        )


@router.get("/projects/{project_id}/gates/{gate_number}/submission")
async def get_gate_submission(
    project_id: uuid.UUID,
    gate_number: int,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    submission = session.exec(
        select(GateSubmission).where(
            GateSubmission.project_id == project_id,
            GateSubmission.gate_number == gate_number,
        )
    ).first()
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gate submission not found",
        )
    rows = _rows_for(session, submission.id)
    return ok(
        serialize_gate_submission(submission, rows, _evidence_by_row(session, rows))
    )


@router.post("/projects/{project_id}/gates/{gate_number}/submission")
async def upsert_gate_submission(
    project_id: uuid.UUID,
    gate_number: int,
    payload: GateSubmissionPayload,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_role(current_user, "client", "security_reviewer", "admin")
    get_project_or_404(project_id, session, current_user)
    submission = _get_or_create_submission(project_id, gate_number, session)
    if payload.intake_payload:
        submission.intake_payload = payload.intake_payload
    for row_payload in payload.requirements:
        session.add(
            RequirementRow(
                gate_submission_id=submission.id,
                requirement_id=row_payload.get("requirement_id"),
                domain=row_payload.get("domain"),
                requirement_text=str(row_payload.get("requirement_text") or ""),
                organization_guidance=row_payload.get("organization_guidance"),
                applicability=row_payload.get("applicability"),
                risk_level=row_payload.get("risk_level"),
                scd_extras=row_payload.get("scd_extras") or {},
            )
        )
    _seed_gate3_rows(submission, session)
    session.add(submission)
    write_audit_event(
        session,
        actor=current_user,
        action="gate.submission.update",
        resource_type="gate_submission",
        resource_id=str(submission.id),
        details={"gate_number": gate_number},
    )
    session.commit()
    rows = _rows_for(session, submission.id)
    return ok(
        serialize_gate_submission(submission, rows, _evidence_by_row(session, rows))
    )


@router.post("/projects/{project_id}/gates/{gate_number}/submit")
async def submit_gate(
    project_id: uuid.UUID,
    gate_number: int,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    submission = _get_or_create_submission(project_id, gate_number, session)
    transition = (submission.status, GateStatus.pending.value)
    allowed_roles = GATE_STATUS_TRANSITIONS.get(transition)
    if allowed_roles is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transition '{transition[0]}' -> '{transition[1]}' is not allowed.",
        )
    ensure_role(current_user, *allowed_roles)
    submission.status = GateStatus.pending.value
    submission.submitted_at = datetime.now(UTC)
    submission.submitted_by_id = current_user.id
    session.add(submission)
    write_audit_event(
        session,
        actor=current_user,
        action="gate.submit",
        resource_type="gate_submission",
        resource_id=str(submission.id),
        details={"gate_number": gate_number},
    )
    session.commit()
    rows = _rows_for(session, submission.id)
    return ok(
        serialize_gate_submission(submission, rows, _evidence_by_row(session, rows))
    )


@router.post("/projects/{project_id}/gates/{gate_number}/review")
async def review_gate(
    project_id: uuid.UUID,
    gate_number: int,
    payload: GateReviewPayload,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    submission = _get_or_create_submission(project_id, gate_number, session)
    transition = (submission.status, payload.status)
    allowed_roles = GATE_STATUS_TRANSITIONS.get(transition)
    if allowed_roles is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transition '{transition[0]}' -> '{transition[1]}' is not allowed.",
        )
    ensure_role(current_user, *allowed_roles)
    if submission.submitted_by_id is not None and (
        submission.submitted_by_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The submitter cannot review the same gate submission.",
        )
    if transition in COMMENT_REQUIRED_TRANSITIONS and not payload.reviewer_comments:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reviewer comments are required for this transition.",
        )
    submission.status = payload.status
    submission.reviewer_comments = payload.reviewer_comments
    submission.reviewed_by_id = current_user.id
    submission.reviewed_at = datetime.now(UTC)
    session.add(submission)
    write_audit_event(
        session,
        actor=current_user,
        action="gate.review",
        resource_type="gate_submission",
        resource_id=str(submission.id),
        details={"from": transition[0], "to": transition[1]},
    )
    session.commit()
    rows = _rows_for(session, submission.id)
    return ok(
        serialize_gate_submission(submission, rows, _evidence_by_row(session, rows))
    )


@router.put("/requirement-rows/{row_id}")
async def update_requirement_row(
    row_id: uuid.UUID,
    payload: RequirementRowUpdate,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    row = session.get(RequirementRow, row_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement row not found",
        )
    _project_for_row(row, session, current_user)
    ensure_role(current_user, "security_reviewer", "security_approver", "admin")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    session.add(row)
    write_audit_event(
        session,
        actor=current_user,
        action="requirement.review.update",
        resource_type="requirement_row",
        resource_id=str(row.id),
        details={"fields": sorted(payload.model_dump(exclude_unset=True))},
    )
    session.commit()
    session.refresh(row)
    evidence = session.exec(
        select(EvidenceItem).where(EvidenceItem.requirement_row_id == row.id)
    ).all()
    return ok(serialize_requirement_row(row, evidence))


@router.post("/requirement-rows/{row_id}/evidence")
async def add_requirement_evidence(
    row_id: uuid.UUID,
    payload: RequirementEvidenceRequest,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    row = session.get(RequirementRow, row_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement row not found",
        )
    _project_for_row(row, session, current_user)
    ensure_role(current_user, "client", "security_reviewer", "admin")
    item = EvidenceItem(
        requirement_row_id=row.id,
        evidence_type=EvidenceType(payload.evidence_type).value,
        content=payload.content,
        file_path=payload.file_path,
        url=payload.url,
    )
    session.add(item)
    write_audit_event(
        session,
        actor=current_user,
        action="requirement.evidence.add",
        resource_type="requirement_row",
        resource_id=str(row.id),
        details={"evidence_type": payload.evidence_type},
    )
    session.commit()
    session.refresh(item)
    evidence = session.exec(
        select(EvidenceItem).where(EvidenceItem.requirement_row_id == row.id)
    ).all()
    return ok(serialize_requirement_row(row, evidence))
