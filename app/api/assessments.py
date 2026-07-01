"""Assessment REST API backed by the shared assessment task service."""

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.agent.orchestrator import run_assessment
from app.core.config import settings
from app.core.deps import require_roles
from app.core.guardrails import sanitize_input
from app.kb.service import get_kb_service
from app.models.assessment import (
    AssessmentTaskCreated,
    AssessmentTaskResult,
    RemediationTracking,
    TrackedRemediation,
)
from app.parser import parse_file
from app.services.assessment_service import (
    InvalidTaskStateError,
    TaskNotFoundError,
    assessment_service,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])

ASSESSMENT_SUBMIT_ROLES = (
    "admin",
    "auditor",
    "user",
    "client",
    "security_reviewer",
)
ASSESSMENT_REVIEW_ROLES = (
    "admin",
    "auditor",
    "security_reviewer",
    "security_approver",
)
ASSESSMENT_SUBMIT_DEP = Depends(require_roles(*ASSESSMENT_SUBMIT_ROLES))
ASSESSMENT_REVIEW_DEP = Depends(require_roles(*ASSESSMENT_REVIEW_ROLES))


class ReviewActionRequest(BaseModel):
    action: Literal["approve", "reject", "comment", "escalate"]
    comment: str | None = None
    assignee: str | None = None


class CommentRequest(BaseModel):
    content: str
    user_id: str = "anonymous"


class RemediationTrackingUpdateRequest(BaseModel):
    status: Literal["open", "in_progress", "resolved", "verified", "closed"] | None = (
        None
    )
    owner: str | None = None
    due_at: datetime | None = None
    external_ticket: str | None = None
    notes: str | None = None
    evidence_refs: list[str] | None = None


AssessmentPhase = Literal[
    "auto",
    "requirements",
    "design",
    "development",
    "testing",
    "deployment",
    "operations",
    "full_ssdlc",
]


def _not_found(exc: TaskNotFoundError) -> HTTPException:
    return HTTPException(404, "Task not found")


@router.post("", response_model=AssessmentTaskCreated)
async def submit_assessment(
    files: list[UploadFile] = File(  # noqa: B008
        ..., description="Documents to assess"
    ),
    scenario_id: str | None = Form(None),
    project_id: str | None = Form(None),
    phase: AssessmentPhase = Form("auto"),  # noqa: B008
    skill_id: str | None = Form(None),
    collaborative_mode: bool = Form(True),
    _current_user: Any = ASSESSMENT_SUBMIT_DEP,
):
    """Submit an assessment task; returns task_id immediately for polling."""
    if len(files) > settings.UPLOAD_MAX_FILES:
        raise HTTPException(413, f"Max {settings.UPLOAD_MAX_FILES} files allowed")

    parsed_documents = []
    for file in files:
        content = await file.read()
        if len(content) > settings.upload_max_bytes:
            raise HTTPException(
                413,
                f"File {file.filename} exceeds {settings.UPLOAD_MAX_FILE_SIZE_MB}MB",
            )
        try:
            parsed = parse_file(content, file.filename or "unknown")
            parsed.metadata.scenario_id = scenario_id
            parsed.metadata.ssdlc_phase_hint = phase
            sanitize_input(parsed.content if isinstance(parsed.content, str) else "")
            parsed_documents.append(parsed)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    return await assessment_service.submit(
        parsed_documents,
        scenario_id=scenario_id,
        project_id=project_id,
        phase=phase,
        skill_id=skill_id,
        collaborative_mode=collaborative_mode,
        runner=run_assessment,
        source="rest",
    )


@router.get("", response_model=list[AssessmentTaskResult])
async def list_assessments(
    status: str | None = Query(None),
    assignee: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    statuses = (
        {item.strip() for item in status.split(",") if item.strip()} if status else None
    )
    return assessment_service.list(
        statuses=statuses,
        assignee=assignee,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=AssessmentTaskResult)
async def get_assessment_result(task_id: str):
    try:
        return assessment_service.get(task_id)
    except TaskNotFoundError as exc:
        raise _not_found(exc) from exc


@router.get("/{task_id}/remediations", response_model=list[TrackedRemediation])
async def list_tracked_remediations(task_id: str):
    try:
        return assessment_service.list_remediations(task_id)
    except TaskNotFoundError as exc:
        raise _not_found(exc) from exc
    except InvalidTaskStateError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post(
    "/{task_id}/remediations/{remediation_id}",
    response_model=RemediationTracking,
)
async def update_remediation_tracking(
    task_id: str,
    remediation_id: str,
    body: RemediationTrackingUpdateRequest,
    _current_user: Any = ASSESSMENT_REVIEW_DEP,
):
    try:
        return assessment_service.update_remediation(
            task_id,
            remediation_id,
            body.model_dump(exclude_unset=True),
        )
    except TaskNotFoundError as exc:
        detail = (
            "Remediation not found"
            if exc.args and exc.args[0] == remediation_id
            else "Task not found"
        )
        raise HTTPException(404, detail) from exc
    except InvalidTaskStateError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/{task_id}/review")
async def review_assessment(
    task_id: str,
    body: ReviewActionRequest,
    _current_user: Any = ASSESSMENT_REVIEW_DEP,
):
    try:
        status = assessment_service.review(
            task_id,
            action=body.action,
            comment=body.comment,
            assignee=body.assignee,
        )
    except TaskNotFoundError as exc:
        raise _not_found(exc) from exc
    except InvalidTaskStateError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"status": status, "task_id": task_id}


@router.get("/{task_id}/activity")
async def get_task_activity(task_id: str):
    try:
        return assessment_service.activity(task_id)
    except TaskNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/{task_id}/comments")
async def add_comment(
    task_id: str,
    body: CommentRequest,
    _current_user: Any = ASSESSMENT_SUBMIT_DEP,
):
    try:
        assessment_service.add_comment(task_id, body.content, body.user_id)
    except TaskNotFoundError as exc:
        raise _not_found(exc) from exc
    return {"message": "Comment added"}


@router.get("/{task_id}/reuse")
async def get_reuse_candidates(task_id: str, top_k: int = 3):
    try:
        task = assessment_service.get(task_id)
    except TaskNotFoundError as exc:
        raise _not_found(exc) from exc
    query_text = f"{task.report.summary if task.report else ''}\n{task_id}"
    try:
        docs = get_kb_service().query_history_responses(query_text, top_k=top_k)
    except Exception:
        docs = []
    return {
        "task_id": task_id,
        "reused_candidates": [
            {"content": item.page_content, "metadata": item.metadata} for item in docs
        ],
    }
