from __future__ import annotations

# ruff: noqa: B008
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.governance import (
    ControlEvidenceItem,
    ControlInstance,
    ControlStatus,
)

from .utils import ok, serialize_control, serialize_control_evidence

router = APIRouter(
    prefix="/projects/{project_id}/controls",
    tags=["governance-controls"],
)


class AddEvidenceRequest(BaseModel):
    evidence_type: Literal["text", "image", "link"] = "text"
    content: str | None = None
    file_path: str | None = None
    url: str | None = None


class HumanReviewRequest(BaseModel):
    decision: Literal["approved", "rejected", "needs_clarification"]
    notes: str | None = None
    reviewer_id: int | None = None


def _load_control(
    project_id: uuid.UUID,
    control_id: str,
    session: Session,
) -> ControlInstance:
    control = session.exec(
        select(ControlInstance).where(
            ControlInstance.project_id == project_id,
            ControlInstance.control_id == control_id,
        )
    ).first()
    if control is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found",
        )
    return control


@router.post("/{control_id}/evidence")
async def add_evidence(
    project_id: uuid.UUID,
    control_id: str,
    payload: AddEvidenceRequest,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    control = _load_control(project_id, control_id, session)
    item = ControlEvidenceItem(
        control_instance_id=control.id,
        evidence_type=payload.evidence_type,
        content=payload.content,
        file_path=payload.file_path,
        url=payload.url,
    )
    session.add(item)
    control.status = ControlStatus.evidence_submitted.value
    session.add(control)
    session.commit()
    session.refresh(item)
    return ok(serialize_control_evidence(item))


@router.get("/{control_id}/evidence")
async def list_evidence(
    project_id: uuid.UUID,
    control_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    control = _load_control(project_id, control_id, session)
    items = session.exec(
        select(ControlEvidenceItem).where(
            ControlEvidenceItem.control_instance_id == control.id
        )
    ).all()
    return ok(
        [serialize_control_evidence(item) for item in items], {"count": len(items)}
    )


@router.post("/{control_id}/human-review")
async def submit_human_review(
    project_id: uuid.UUID,
    control_id: str,
    payload: HumanReviewRequest,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    control = _load_control(project_id, control_id, session)
    control.human_decision = payload.decision
    control.human_notes = payload.notes
    control.human_reviewer_id = payload.reviewer_id
    control.human_reviewed_at = datetime.now(UTC)
    control.status = payload.decision
    session.add(control)
    session.commit()
    session.refresh(control)
    return ok(serialize_control(control))


@router.get("/{control_id}/review-history")
async def get_review_history(
    project_id: uuid.UUID,
    control_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    control = _load_control(project_id, control_id, session)
    history = []
    if control.ai_reviewed_at:
        history.append(
            {
                "type": "ai_review",
                "at": control.ai_reviewed_at.isoformat(),
                "score": control.ai_score,
                "rationale": control.ai_rationale,
                "confidence": control.ai_confidence,
            }
        )
    if control.human_reviewed_at:
        history.append(
            {
                "type": "human_review",
                "at": control.human_reviewed_at.isoformat(),
                "decision": control.human_decision,
                "notes": control.human_notes,
            }
        )
    return ok(history, {"count": len(history)})
