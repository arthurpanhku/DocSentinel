from __future__ import annotations

# ruff: noqa: B008
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.security import ensure_role
from app.models.governance import (
    SubAgentRun,
    SubAgentStatus,
)
from app.models.governance.sub_agent_run import COMMENT_REQUIRED, STATUS_ROLE_MAP

from .utils import get_project_or_404, iso, ok, write_audit_event

router = APIRouter(
    prefix="/projects/{project_id}/sub-agents",
    tags=["governance-sub-agents"],
)


class SubAgentStatusUpdate(BaseModel):
    status: SubAgentStatus
    comment: str | None = None
    actor_id: int | None = None  # Deprecated: authenticated actor is used.
    actor_role: str | None = None  # Deprecated: authenticated role is used.


def _serialize_run(run: SubAgentRun) -> dict[str, Any]:
    return {
        "id": str(run.id),
        "project_id": str(run.project_id),
        "gate": run.gate,
        "sub_agent_key": run.sub_agent_key,
        "status": run.status,
        "actor_id": run.actor_id,
        "comment": run.comment,
        "run_output": run.run_output or {},
        "last_transitioned_at": iso(run.last_transitioned_at),
        "created_at": iso(run.created_at),
        "updated_at": iso(run.updated_at),
    }


def _get_or_create_run(
    session: Session,
    project_id: uuid.UUID,
    gate: str,
    sub_agent_key: str,
) -> SubAgentRun:
    run = session.exec(
        select(SubAgentRun).where(
            SubAgentRun.project_id == project_id,
            SubAgentRun.gate == gate,
            SubAgentRun.sub_agent_key == sub_agent_key,
        )
    ).first()
    if run is None:
        run = SubAgentRun(
            project_id=project_id,
            gate=gate,
            sub_agent_key=sub_agent_key,
            status=SubAgentStatus.empty.value,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
    return run


@router.get("")
async def list_sub_agent_runs(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    runs = session.exec(
        select(SubAgentRun).where(SubAgentRun.project_id == project_id)
    ).all()
    return ok([_serialize_run(run) for run in runs], {"count": len(runs)})


@router.get("/{gate}/{key}")
async def get_sub_agent_run(
    project_id: uuid.UUID,
    gate: str,
    key: str,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    run = _get_or_create_run(session, project_id, gate, key)
    return ok(_serialize_run(run))


@router.patch("/{gate}/{key}/status")
async def update_sub_agent_status(
    project_id: uuid.UUID,
    gate: str,
    key: str,
    payload: SubAgentStatusUpdate,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    run = _get_or_create_run(session, project_id, gate, key)
    new_status = payload.status.value
    old_status = str(run.status)
    if not run.can_transition_to(new_status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Transition '{old_status}' -> '{new_status}' is not allowed.",
        )
    if new_status in COMMENT_REQUIRED and not (payload.comment or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A comment is required when setting status to '{new_status}'.",
        )
    allowed_roles = STATUS_ROLE_MAP.get(new_status, set())
    if allowed_roles:
        ensure_role(current_user, *allowed_roles)
    run.status = new_status
    run.actor_id = current_user.id
    run.comment = payload.comment
    run.last_transitioned_at = datetime.now(UTC)
    session.add(run)
    write_audit_event(
        session,
        actor=current_user,
        action="sub_agent.status.update",
        resource_type="sub_agent_run",
        resource_id=str(run.id),
        details={"from": old_status, "to": new_status},
    )
    session.commit()
    session.refresh(run)
    return ok(_serialize_run(run))


@router.post("/{gate}/{key}/output")
async def save_sub_agent_output(
    project_id: uuid.UUID,
    gate: str,
    key: str,
    output: dict[str, Any],
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_role(current_user, "security_reviewer", "admin")
    get_project_or_404(project_id, session, current_user)
    run = _get_or_create_run(session, project_id, gate, key)
    run.run_output = output
    if run.status == SubAgentStatus.empty.value:
        run.status = SubAgentStatus.draft.value
        run.last_transitioned_at = datetime.now(UTC)
    session.add(run)
    write_audit_event(
        session,
        actor=current_user,
        action="sub_agent.output.save",
        resource_type="sub_agent_run",
        resource_id=str(run.id),
    )
    session.commit()
    session.refresh(run)
    return ok(_serialize_run(run))
