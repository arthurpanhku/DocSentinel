"""
Assessment API: submit task, get result.
PRD §6; docs/02-api-specification.yaml.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.agent.orchestrator import run_assessment
from app.core.config import settings
from app.core.guardrails import sanitize_input
from app.kb.service import get_kb_service
from app.models.assessment import AssessmentTaskCreated, AssessmentTaskResult
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
        _tasks[task_id_str].update({
            "status": target_status,
            "report": report.model_dump(),
            "completed_at": now,
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
