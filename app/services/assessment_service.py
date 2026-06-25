"""Shared assessment task lifecycle for REST, MCP, and A2A entry points."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.agent.orchestrator import run_assessment
from app.kb.service import get_kb_service
from app.models.assessment import (
    AssessmentReport,
    AssessmentTaskCreated,
    AssessmentTaskResult,
    Remediation,
    RemediationTracking,
    TrackedRemediation,
)
from app.models.parser import ParsedDocument

logger = logging.getLogger(__name__)

AssessmentRunner = Callable[..., Awaitable[AssessmentReport]]
TERMINAL_STATUSES = {
    "review_pending",
    "approved",
    "rejected",
    "escalated",
    "completed",
    "failed",
}


class TaskNotFoundError(KeyError):
    """Raised when an assessment task does not exist."""


class InvalidTaskStateError(ValueError):
    """Raised when an operation is invalid for the current task state."""


class AssessmentService:
    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}

    def clear(self) -> None:
        self._tasks.clear()

    async def submit(
        self,
        parsed_documents: list[ParsedDocument],
        *,
        scenario_id: str | None = None,
        project_id: str | None = None,
        phase: str = "auto",
        skill_id: str | None = None,
        collaborative_mode: bool = True,
        runner: AssessmentRunner = run_assessment,
        source: str = "rest",
    ) -> AssessmentTaskCreated:
        task_id = uuid4()
        task_id_str = str(task_id)
        created_at = datetime.now(timezone.utc)
        self._tasks[task_id_str] = {
            "task_id": task_id,
            "status": "pending",
            "created_at": created_at,
            "version": 1,
            "phase": phase,
            "source": source,
            "activity": [
                {
                    "type": "task_created",
                    "at": created_at.isoformat(),
                    "message": f"Assessment task created via {source}",
                }
            ],
            "revisions": [],
            "comments": [],
            "remediation_tracking": {},
        }
        asyncio.create_task(
            self._run(
                task_id_str,
                task_id,
                parsed_documents,
                scenario_id,
                project_id,
                phase,
                skill_id,
                collaborative_mode,
                runner,
            )
        )
        return AssessmentTaskCreated(
            task_id=task_id,
            status="accepted",
            message="Assessment task created.",
        )

    async def _run(
        self,
        task_id_str: str,
        task_id: UUID,
        parsed_documents: list[ParsedDocument],
        scenario_id: str | None,
        project_id: str | None,
        phase: str,
        skill_id: str | None,
        collaborative_mode: bool,
        runner: AssessmentRunner,
    ) -> None:
        task = self._tasks[task_id_str]
        task["status"] = "running"
        task["activity"].append(
            {
                "type": "assessment_started",
                "at": datetime.now(timezone.utc).isoformat(),
                "message": "Assessment processing started",
            }
        )
        try:
            report = await runner(
                task_id,
                parsed_documents,
                scenario_id=scenario_id,
                project_id=project_id,
                phase=phase,
                skill_id=skill_id,
            )
            if report.metadata:
                report.metadata.ssdlc_stage = phase
                report.metadata.ssdlc_phase = phase
                report.metadata.skill_id = skill_id
            report.phase = phase
            target_status = "review_pending" if collaborative_mode else "completed"
            now = datetime.now(timezone.utc)
            tracking = {
                item.id: RemediationTracking(
                    remediation_id=item.id,
                    updated_at=now,
                ).model_dump()
                for item in report.remediations
            }
            task.update(
                {
                    "status": target_status,
                    "report": report.model_dump(),
                    "completed_at": now,
                    "remediation_tracking": tracking,
                }
            )
            task["revisions"].append(
                {
                    "version": 1,
                    "status": target_status,
                    "updated_at": now.isoformat(),
                    "report": report.model_dump(),
                }
            )
            task["activity"].append(
                {
                    "type": "draft_generated",
                    "at": now.isoformat(),
                    "message": "AI generated draft report",
                }
            )
            self._index_history(task_id_str, scenario_id, report)
        except Exception as exc:
            logger.exception("Assessment %s failed", task_id_str)
            task["status"] = "failed"
            task["error"] = str(exc)
            task["completed_at"] = datetime.now(timezone.utc)

    def _index_history(
        self,
        task_id: str,
        scenario_id: str | None,
        report: AssessmentReport,
    ) -> None:
        try:
            get_kb_service().add_history_response(
                task_id=task_id,
                version=self._tasks[task_id]["version"],
                scenario_id=scenario_id,
                report_json=report.model_dump(),
            )
        except Exception:
            self._tasks[task_id]["activity"].append(
                {
                    "type": "history_index_skipped",
                    "at": datetime.now(timezone.utc).isoformat(),
                    "message": "History indexing unavailable in current runtime",
                }
            )

    def _record(self, task_id: str) -> dict[str, Any]:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(task_id) from None

    def get(self, task_id: str) -> AssessmentTaskResult:
        task = self._record(task_id)
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

    def list(
        self,
        *,
        statuses: set[str] | None = None,
        assignee: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AssessmentTaskResult]:
        tasks = [
            task
            for task in self._tasks.values()
            if (not statuses or task.get("status") in statuses)
            and (not assignee or task.get("assignee") == assignee)
        ]
        tasks.sort(
            key=lambda task: task.get("created_at") or datetime.min,
            reverse=True,
        )
        return [
            self.get(str(task["task_id"]))
            for task in tasks[offset : offset + limit]
        ]

    async def wait_for_terminal(
        self,
        task_id: str,
        timeout_seconds: int,
    ) -> AssessmentTaskResult:
        async def poll() -> AssessmentTaskResult:
            while True:
                result = self.get(task_id)
                if result.status in TERMINAL_STATUSES:
                    return result
                await asyncio.sleep(0.05)

        return await asyncio.wait_for(poll(), timeout=timeout_seconds)

    def activity(self, task_id: str) -> list[dict[str, Any]]:
        return list(self._record(task_id).get("activity", []))

    def add_comment(self, task_id: str, content: str, user_id: str) -> None:
        task = self._record(task_id)
        now = datetime.now(timezone.utc)
        task["comments"].append(
            {"content": content, "user_id": user_id, "at": now.isoformat()}
        )
        task["activity"].append(
            {
                "type": "comment_added",
                "at": now.isoformat(),
                "preview": content[:50],
            }
        )

    def review(
        self,
        task_id: str,
        *,
        action: str,
        comment: str | None,
        assignee: str | None,
    ) -> str:
        task = self._record(task_id)
        current_status = task["status"]
        if current_status not in {"review_pending", "escalated"}:
            raise InvalidTaskStateError(
                f"Cannot review task in status {current_status}"
            )
        status_by_action = {
            "approve": "approved",
            "reject": "rejected",
            "escalate": "escalated",
        }
        new_status = status_by_action.get(action, current_status)
        task["status"] = new_status
        if assignee:
            task["assignee"] = assignee
        now = datetime.now(timezone.utc)
        task["activity"].append(
            {
                "type": "review_action",
                "action": action,
                "at": now.isoformat(),
                "comment": comment,
                "assignee": assignee,
            }
        )
        if comment:
            task["comments"].append(
                {"content": comment, "at": now.isoformat(), "action": action}
            )
        return new_status

    def list_remediations(self, task_id: str) -> list[TrackedRemediation]:
        task = self._record(task_id)
        report = task.get("report")
        if not report:
            raise InvalidTaskStateError("Report not available")
        tracking = task.get("remediation_tracking") or {}
        return [
            TrackedRemediation(
                remediation=remediation,
                tracking=RemediationTracking.model_validate(
                    tracking.get(remediation.id)
                    or RemediationTracking(remediation_id=remediation.id)
                ),
            )
            for remediation in (
                Remediation.model_validate(item)
                for item in report.get("remediations", [])
            )
        ]

    def update_remediation(
        self,
        task_id: str,
        remediation_id: str,
        update: dict[str, Any],
    ) -> RemediationTracking:
        task = self._record(task_id)
        report = task.get("report")
        if not report:
            raise InvalidTaskStateError("Report not available")
        remediation_ids = {
            item.get("id") for item in report.get("remediations", []) if item.get("id")
        }
        if remediation_id not in remediation_ids:
            raise TaskNotFoundError(remediation_id)
        tracking = task.setdefault("remediation_tracking", {})
        existing = RemediationTracking.model_validate(
            tracking.get(remediation_id)
            or RemediationTracking(remediation_id=remediation_id)
        ).model_dump()
        if update.get("evidence_refs") is None:
            update.pop("evidence_refs", None)
        existing.update(update)
        existing["updated_at"] = datetime.now(timezone.utc)
        tracking[remediation_id] = existing
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


assessment_service = AssessmentService()
