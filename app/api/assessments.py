"""
Assessment API: submit task, get result.
PRD §6; docs/02-api-specification.yaml.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.agent.orchestrator import run_assessment
from app.core.config import settings
from app.core.guardrails import sanitize_input
from app.kb.service import get_kb_service
from app.models.assessment import AssessmentTaskCreated, AssessmentTaskResult, Remediation
from app.parser import parse_file

router = APIRouter(prefix="/assessments", tags=["assessments"])
logger = logging.getLogger(__name__)


class ReviewActionRequest(BaseModel):
    action: Literal["approve", "reject", "comment", "escalate"]
    comment: str | None = None
    assignee: str | None = None


class CommentRequest(BaseModel):
    content: str
    user_id: str = "anonymous"


class RemediationTracking(BaseModel):
    remediation_id: str
    status: Literal["open", "in_progress", "resolved", "verified", "closed"] = "open"
    owner: str | None = None
    due_at: datetime | None = None
    external_ticket: str | None = None
    notes: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class RemediationTrackingUpdateRequest(BaseModel):
    status: Literal["open", "in_progress", "resolved", "verified", "closed"] | None = None
    owner: str | None = None
    due_at: datetime | None = None
    external_ticket: str | None = None
    notes: str | None = None
    evidence_refs: list[str] | None = None


class TrackedRemediation(BaseModel):
    remediation: Remediation
    tracking: RemediationTracking


# In-memory task store (MVP — see TODO #9 for persistent storage)
_tasks: dict = {}


async def _run_assessment_background(
    task_id_str: str,
    task_id,
    parsed_list: list,
    scenario_id: str | None,
    project_id: str | None,
    skill_id: str | None,
    collaborative_mode: bool,
) -> None:
    """Execute assessment in the background and update the task store."""
    _tasks[task_id_str]["status"] = "running"
    _tasks[task_id_str]["activity"].append({
        "type": "assessment_started",
        "at": datetime.now(timezone.utc).isoformat(),
        "message": "Assessment processing started",
    })

    try:
        report = await run_assessment(
            task_id,
            parsed_list,
            scenario_id=scenario_id,
            project_id=project_id,
            skill_id=skill_id,
        )
        target_status = "review_pending" if collaborative_mode else "completed"
        now = datetime.now(timezone.utc)
        remediation_tracking = {}
        for r in report.remediations:
            remediation_tracking[r.id] = {
                "remediation_id": r.id,
                "status": "open",
                "owner": None,
                "due_at": None,
                "external_ticket": None,
                "notes": None,
                "evidence_refs": [],
                "updated_at": now,
            }
        _tasks[task_id_str].update({
            "status": target_status,
            "report": report.model_dump(),
            "completed_at": now,
            "remediation_tracking": remediation_tracking,
        })
        _tasks[task_id_str]["revisions"].append({
            "version": 1,
            "status": target_status,
            "updated_at": now.isoformat(),
            "report": report.model_dump(),
        })
        _tasks[task_id_str]["activity"].append({
            "type": "draft_generated",
            "at": now.isoformat(),
            "message": "AI generated draft report",
        })

        try:
            kb = get_kb_service()
            kb.add_history_response(
                task_id=task_id_str,
                version=_tasks[task_id_str]["version"],
                scenario_id=scenario_id,
                report_json=report.model_dump(),
            )
        except Exception:
            _tasks[task_id_str]["activity"].append({
                "type": "history_index_skipped",
                "at": datetime.now(timezone.utc).isoformat(),
                "message": "History indexing unavailable in current runtime",
            })
    except Exception as e:
        logger.exception("Assessment %s failed", task_id_str)
        _tasks[task_id_str]["status"] = "failed"
        _tasks[task_id_str]["error"] = str(e)
        _tasks[task_id_str]["completed_at"] = datetime.now(timezone.utc)


@router.post("", response_model=AssessmentTaskCreated)
async def submit_assessment(
    files: list[UploadFile] = File(  # noqa: B008
        ..., description="Documents to assess"
    ),
    scenario_id: str | None = Form(None),
    project_id: str | None = Form(None),
    skill_id: str | None = Form(None),
    collaborative_mode: bool = Form(True),
):
    """Submit an assessment task; returns task_id immediately for polling."""

    if len(files) > settings.UPLOAD_MAX_FILES:
        raise HTTPException(413, f"Max {settings.UPLOAD_MAX_FILES} files allowed")

    parsed_list = []
    for file in files:
        content = await file.read()
        if len(content) > settings.UPLOAD_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                413,
                f"File {file.filename} exceeds {settings.UPLOAD_MAX_FILE_SIZE_MB}MB",
            )
        try:
            parsed = parse_file(content, file.filename or "unknown")
            parsed.metadata.scenario_id = scenario_id
            sanitize_input(parsed.content if isinstance(parsed.content, str) else "")
            parsed_list.append(parsed)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    task_id = uuid4()
    task_id_str = str(task_id)
    created_at = datetime.now(timezone.utc)
    _tasks[task_id_str] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": created_at,
        "version": 1,
        "activity": [
            {
                "type": "task_created",
                "at": created_at.isoformat(),
                "message": "Assessment task created",
            }
        ],
        "revisions": [],
        "comments": [],
        "remediation_tracking": {},
    }

    asyncio.create_task(
        _run_assessment_background(
            task_id_str, task_id, parsed_list,
            scenario_id, project_id, skill_id, collaborative_mode,
        )
    )

    return AssessmentTaskCreated(
        task_id=task_id,
        status="accepted",
        message=(
            "Assessment task created. Use GET /assessments/{task_id} "
            "to retrieve the result."
        ),
    )


@router.get("", response_model=list[AssessmentTaskResult])
async def list_assessments(
    status: str | None = Query(None),
    assignee: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    statuses = None
    if status:
        statuses = {s.strip() for s in status.split(",") if s.strip()}

    tasks = []
    for task_id, task in _tasks.items():
        if statuses and task.get("status") not in statuses:
            continue
        if assignee and task.get("assignee") != assignee:
            continue
        tasks.append((task_id, task))

    tasks.sort(key=lambda t: t[1].get("created_at") or datetime.min, reverse=True)
    sliced = tasks[offset : offset + limit]

    results: list[AssessmentTaskResult] = []
    for task_id, task in sliced:
        results.append(
            AssessmentTaskResult(
                task_id=task["task_id"],
                status=task["status"],
                report=task.get("report"),
                error_message=task.get("error"),
                created_at=task["created_at"],
                completed_at=task.get("completed_at"),
                version=task.get("version", 1),
                assignee=task.get("assignee"),
                comments=task.get("comments", []),
            )
        )
    return results


@router.get("/{task_id}", response_model=AssessmentTaskResult)
async def get_assessment_result(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")
    task = _tasks[task_id]

    # Map raw dict to Pydantic model
    return AssessmentTaskResult(
        task_id=task["task_id"],
        status=task["status"],
        report=task.get("report"),
        error_message=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        version=task.get("version", 1),
        assignee=task.get("assignee"),
        comments=task.get("comments", []),
    )


@router.get("/{task_id}/remediations", response_model=list[TrackedRemediation])
async def list_tracked_remediations(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")
    task = _tasks[task_id]
    report = task.get("report")
    if not report:
        raise HTTPException(400, "Report not available")

    track = task.get("remediation_tracking") or {}
    items = []
    for r in report.get("remediations", []):
        remediation = Remediation.model_validate(r)
        tracking_raw = track.get(remediation.id)
        if not tracking_raw:
            tracking_raw = {
                "remediation_id": remediation.id,
                "status": "open",
                "owner": None,
                "due_at": None,
                "external_ticket": None,
                "notes": None,
                "evidence_refs": [],
                "updated_at": None,
            }
        items.append(
            TrackedRemediation(
                remediation=remediation,
                tracking=RemediationTracking.model_validate(tracking_raw),
            )
        )
    return items


@router.post("/{task_id}/remediations/{remediation_id}", response_model=RemediationTracking)
async def update_remediation_tracking(
    task_id: str, remediation_id: str, body: RemediationTrackingUpdateRequest
):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")
    task = _tasks[task_id]
    report = task.get("report")
    if not report:
        raise HTTPException(400, "Report not available")

    remediations = {r.get("id") for r in report.get("remediations", []) if r.get("id")}
    if remediation_id not in remediations:
        raise HTTPException(404, "Remediation not found")

    track = task.setdefault("remediation_tracking", {})
    existing = track.get(remediation_id) or {
        "remediation_id": remediation_id,
        "status": "open",
        "owner": None,
        "due_at": None,
        "external_ticket": None,
        "notes": None,
        "evidence_refs": [],
        "updated_at": None,
    }

    update = body.model_dump(exclude_unset=True)
    if "evidence_refs" in update and update["evidence_refs"] is None:
        update.pop("evidence_refs", None)
    existing.update(update)
    existing["updated_at"] = datetime.now(timezone.utc)
    track[remediation_id] = existing

    task["activity"].append(
        {
            "type": "remediation_tracking_updated",
            "at": existing["updated_at"].isoformat(),
            "remediation_id": remediation_id,
            "status": existing.get("status"),
            "owner": existing.get("owner"),
            "external_ticket": existing.get("external_ticket"),
        }
    )

    return RemediationTracking.model_validate(existing)


@router.post("/{task_id}/review")
async def review_assessment(task_id: str, body: ReviewActionRequest):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")

    task = _tasks[task_id]
    current_status = task["status"]

    if current_status not in ["review_pending", "escalated"]:
        raise HTTPException(400, f"Cannot review task in status {current_status}")

    new_status = current_status
    activity_type = "review_action"

    if body.action == "approve":
        new_status = "approved"
    elif body.action == "reject":
        new_status = "rejected"
    elif body.action == "escalate":
        new_status = "escalated"
    elif body.action == "comment":
        pass  # Status doesn't change

    # Update task
    task["status"] = new_status
    if body.assignee:
        task["assignee"] = body.assignee

    # Add activity
    task["activity"].append({
        "type": activity_type,
        "action": body.action,
        "at": datetime.now(timezone.utc).isoformat(),
        "comment": body.comment,
        "assignee": body.assignee
    })

    # Add comment if provided
    if body.comment:
        task["comments"].append({
            "content": body.comment,
            "at": datetime.now(timezone.utc).isoformat(),
            "action": body.action
        })

    return {"status": new_status, "task_id": task_id}


@router.get("/{task_id}/activity")
async def get_task_activity(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")
    return _tasks[task_id].get("activity", [])


@router.post("/{task_id}/comments")
async def add_comment(task_id: str, body: CommentRequest):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")

    comment_entry = {
        "content": body.content,
        "user_id": body.user_id,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    _tasks[task_id]["comments"].append(comment_entry)
    _tasks[task_id]["activity"].append({
        "type": "comment_added",
        "at": datetime.now(timezone.utc).isoformat(),
        "preview": body.content[:50]
    })
    return {"message": "Comment added"}


@router.get("/{task_id}/reuse")
async def get_reuse_candidates(task_id: str, top_k: int = 3):
    if task_id not in _tasks:
        raise HTTPException(404, "Task not found")
    task = _tasks[task_id]
    report = task.get("report") or {}
    query_text = f"{report.get('summary', '')}\n{task_id}"
    try:
        kb = get_kb_service()
        docs = kb.query_history_responses(query_text, top_k=top_k)
    except Exception:
        docs = []
    return {
        "task_id": task_id,
        "reused_candidates": [
            {"content": d.page_content, "metadata": d.metadata} for d in docs
        ],
    }
