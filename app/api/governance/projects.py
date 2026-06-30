from __future__ import annotations

# ruff: noqa: B008
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.governance import (
    ControlEvidenceItem,
    ControlInstance,
    Project,
)
from app.services.control_generator import (
    generate_controls_for_project,
    summarize_controls,
)
from app.services.pallas_lens import build_pallas_lens
from app.services.policy_pack import list_overlay_packs

from .utils import (
    evidence_count_by_control,
    get_project_or_404,
    ok,
    serialize_control,
    serialize_project,
)

router = APIRouter(prefix="/projects", tags=["governance-projects"])


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    business_owner: str | None = None
    owner_id: int | None = None
    risk_tier: str | None = None
    compliance_frameworks: list[str] = Field(default_factory=list)
    review_mode: str | None = None
    involves_ai_ml: bool | None = None
    ai_risk_class: str | None = None
    slsa_target_level: int | None = None
    system_type: str | None = None
    hosting_type: str | None = None
    data_classification: str | None = None
    risk_level: int | None = None
    organization: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    business_owner: str | None = None
    risk_tier: str | None = None
    compliance_frameworks: list[str] | None = None
    review_mode: str | None = None
    involves_ai_ml: bool | None = None
    ai_risk_class: str | None = None
    slsa_target_level: int | None = None
    status: str | None = None
    system_type: str | None = None
    hosting_type: str | None = None
    data_classification: str | None = None
    risk_level: int | None = None
    organization: str | None = None


class GenerateControlsRequest(BaseModel):
    framework_ids: list[str] = Field(default_factory=list)
    review_mode: Literal["ai_first", "human_only", "ai_only"] | None = None
    regenerate: bool = False


def _derive_control_profile(
    risk_level: int | None, risk_tier: str | None
) -> str | None:
    if risk_tier:
        tier = risk_tier.strip().lower()
        return "full_ssdlc" if tier in {"critical", "high"} else "essential_ssdlc"
    if risk_level is None:
        return None
    return "full_ssdlc" if risk_level <= 3 else "essential_ssdlc"


@router.get("/frameworks")
async def list_compliance_frameworks() -> dict[str, Any]:
    frameworks = list_overlay_packs()
    return ok(frameworks, {"count": len(frameworks)})


@router.get("")
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    projects = session.exec(
        select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
    ).all()
    return ok(
        [serialize_project(project) for project in projects],
        {"skip": skip, "limit": limit, "count": len(projects)},
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    values = payload.model_dump()
    project = Project(
        **values,
        control_profile=_derive_control_profile(
            values.get("risk_level"),
            values.get("risk_tier"),
        ),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    frameworks = list(project.compliance_frameworks or [])
    if frameworks:
        generate_controls_for_project(
            project=project,
            intake_payload={},
            framework_ids=frameworks,
            review_mode=project.review_mode or "ai_first",
            session=session,
            regenerate=False,
        )
        session.refresh(project)
    return ok(serialize_project(project))


@router.get("/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    project = get_project_or_404(project_id, session)
    return ok(serialize_project(project))


@router.put("/{project_id}")
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    project = get_project_or_404(project_id, session)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    if "risk_level" in updates or "risk_tier" in updates:
        project.control_profile = _derive_control_profile(
            project.risk_level,
            project.risk_tier,
        )
    session.add(project)
    session.commit()
    session.refresh(project)
    return ok(serialize_project(project))


@router.post("/{project_id}/generate-controls")
async def generate_controls(
    project_id: uuid.UUID,
    payload: GenerateControlsRequest,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    project = get_project_or_404(project_id, session)
    framework_ids = payload.framework_ids or list(project.compliance_frameworks or [])
    if not framework_ids:
        framework_ids = [item["id"] for item in list_overlay_packs()]
    summary = generate_controls_for_project(
        project=project,
        intake_payload={},
        framework_ids=framework_ids,
        review_mode=payload.review_mode or project.review_mode or "ai_first",
        session=session,
        regenerate=payload.regenerate,
    )
    return ok(summary)


@router.get("/{project_id}/controls")
async def list_controls(
    project_id: uuid.UUID,
    framework_id: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    applicable_only: bool = False,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    get_project_or_404(project_id, session)
    stmt = select(ControlInstance).where(ControlInstance.project_id == project_id)
    if framework_id:
        stmt = stmt.where(ControlInstance.framework_id == framework_id)
    if status_filter:
        stmt = stmt.where(ControlInstance.status == status_filter)
    if applicable_only:
        stmt = stmt.where(ControlInstance.is_applicable.is_(True))
    controls = session.exec(
        stmt.order_by(ControlInstance.framework_id, ControlInstance.control_id)
    ).all()
    counts = evidence_count_by_control(controls, session)
    data = [
        serialize_control(control, counts.get(control.id, 0))
        for control in controls
        if control.id is not None
    ]
    return ok(data, {"count": len(data)})


@router.get("/{project_id}/controls/summary")
async def get_controls_summary(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    get_project_or_404(project_id, session)
    return ok(summarize_controls(project_id, session))


@router.get("/{project_id}/pallas-lens")
async def get_pallas_lens(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    project = get_project_or_404(project_id, session)
    controls = session.exec(
        select(ControlInstance).where(ControlInstance.project_id == project_id)
    ).all()
    lens_controls = []
    for control in controls:
        evidence = []
        if control.id is not None:
            evidence = session.exec(
                select(ControlEvidenceItem).where(
                    ControlEvidenceItem.control_instance_id == control.id
                )
            ).all()
        control_data = control.model_dump()
        control_data["evidence_items"] = evidence
        lens_controls.append(type("LensControl", (), control_data)())
    return ok(build_pallas_lens(project, lens_controls))


@router.get("/{project_id}/gates")
async def list_gates(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    from app.models.governance import GateSubmission

    get_project_or_404(project_id, session)
    submissions = {
        submission.gate_number: submission
        for submission in session.exec(
            select(GateSubmission).where(GateSubmission.project_id == project_id)
        ).all()
    }
    gates = []
    for gate_number in range(1, 7):
        submission = submissions.get(gate_number)
        gates.append(
            {
                "gate_number": gate_number,
                "status": submission.status if submission else None,
                "submission_id": str(submission.id) if submission else None,
            }
        )
    return ok(gates)
