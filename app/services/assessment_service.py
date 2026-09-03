"""Shared assessment task lifecycle for REST, MCP, and A2A entry points."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.agent.orchestrator import run_assessment
from app.agent.task_contract import AgentTaskContract, build_task_contract
from app.core.config import settings
from app.core.db import engine
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
from app.services.assessment_store import (
    AssessmentTaskStore,
    MemoryAssessmentTaskStore,
    SqlAssessmentTaskStore,
    iter_incomplete,
)

logger = logging.getLogger(__name__)

AssessmentRunner = Callable[..., Awaitable[AssessmentReport]]
TERMINAL_STATUSES = {
    "review_pending",
    "approved",
    "rejected",
    "escalated",
    "completed",
    "failed",
    "cancelled",
    "interrupted",
}


class TaskNotFoundError(KeyError):
    """Raised when an assessment task does not exist."""


class InvalidTaskStateError(ValueError):
    """Raised when an operation is invalid for the current task state."""


def _runner_accepts_task_contract(runner: AssessmentRunner) -> bool:
    """Detect the optional contract parameter without executing a runner twice."""
    side_effect = getattr(runner, "side_effect", None)
    target = side_effect if callable(side_effect) else runner
    try:
        parameters = inspect.signature(target).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(
        parameter.name == "task_contract"
        or parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )


class AssessmentService:
    def __init__(self, store: AssessmentTaskStore | None = None) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}
        self._active: dict[str, asyncio.Task] = {}
        if store is not None:
            self._store = store
        elif settings.ASSESSMENT_PERSISTENCE_ENABLED:
            self._store = SqlAssessmentTaskStore(
                engine,
                create_tables=settings.ENABLE_CREATE_ALL,
            )
        else:
            self._store = MemoryAssessmentTaskStore()

    def clear(self) -> None:
        for active in self._active.values():
            active.cancel()
        self._active.clear()
        self._tasks.clear()
        self._store.clear()

    def _save(self, task: dict[str, Any]) -> None:
        task["updated_at"] = datetime.now(UTC)
        self._tasks[str(task["task_id"])] = task
        self._store.save(task)

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
        tenant_id: str = "default",
        submitted_by_id: int | None = None,
        idempotency_key: str | None = None,
    ) -> AssessmentTaskCreated:
        if idempotency_key:
            existing = self._store.find_idempotent(tenant_id, idempotency_key)
            if existing is not None:
                self._tasks[str(existing["task_id"])] = existing
                return AssessmentTaskCreated(
                    task_id=existing["task_id"],
                    status="queued" if existing["status"] == "pending" else "accepted",
                    message="Existing idempotent assessment task returned.",
                    task_contract=existing["task_contract"],
                )
        task_id = uuid4()
        task_id_str = str(task_id)
        created_at = datetime.now(UTC)
        task_contract = build_task_contract(
            task_id=task_id,
            parsed_documents=parsed_documents,
            phase=phase,
            created_at=created_at,
        )
        self._tasks[task_id_str] = {
            "task_id": task_id,
            "status": "pending",
            "created_at": created_at,
            "version": 1,
            "phase": phase,
            "source": source,
            "tenant_id": tenant_id,
            "submitted_by_id": submitted_by_id,
            "idempotency_key": idempotency_key,
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
            "task_contract": task_contract,
            "execution": {
                "parsed_documents": [
                    document.model_dump(mode="json") for document in parsed_documents
                ],
                "scenario_id": scenario_id,
                "project_id": project_id,
                "phase": phase,
                "skill_id": skill_id,
                "collaborative_mode": collaborative_mode,
                "resumable": runner is run_assessment,
                "attempt": 0,
            },
        }
        self._save(self._tasks[task_id_str])
        active = asyncio.create_task(
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
        self._active[task_id_str] = active
        active.add_done_callback(lambda _task: self._active.pop(task_id_str, None))
        return AssessmentTaskCreated(
            task_id=task_id,
            status="accepted",
            message="Assessment task created.",
            task_contract=task_contract,
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
                "at": datetime.now(UTC).isoformat(),
                "message": "Assessment processing started",
            }
        )
        self._save(task)
        try:
            task_contract = AgentTaskContract.model_validate(task["task_contract"])
            runner_kwargs = {
                "scenario_id": scenario_id,
                "project_id": project_id,
                "phase": phase,
                "skill_id": skill_id,
            }
            if _runner_accepts_task_contract(runner):
                runner_kwargs["task_contract"] = task_contract
            attempts = int(task.get("execution", {}).get("attempt", 0))
            retry_limit = int(task_contract.retry_limit)
            while True:
                try:
                    report = await asyncio.wait_for(
                        runner(task_id, parsed_documents, **runner_kwargs),
                        timeout=settings.ASSESSMENT_TASK_TIMEOUT_SECONDS,
                    )
                    break
                except (TimeoutError, ConnectionError) as exc:
                    attempts += 1
                    task["execution"]["attempt"] = attempts
                    task["activity"].append(
                        {
                            "type": "transient_failure",
                            "at": datetime.now(UTC).isoformat(),
                            "attempt": attempts,
                            "message": type(exc).__name__,
                        }
                    )
                    self._save(task)
                    if attempts > retry_limit:
                        raise
            if report.task_contract is None:
                report = report.model_copy(
                    update={"task_contract": task["task_contract"]}
                )
            if report.metadata:
                report.metadata.ssdlc_stage = phase
                report.metadata.ssdlc_phase = phase
                report.metadata.skill_id = skill_id
            report.phase = phase
            target_status = "review_pending" if collaborative_mode else "completed"
            now = datetime.now(UTC)
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
                    "plan_artifact": report.plan_artifact,
                    "evaluation": report.evaluation,
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
            task["execution"]["parsed_documents"] = []
            self._save(task)
            self._index_history(task_id_str, scenario_id, report)
        except asyncio.CancelledError:
            task["status"] = "cancelled"
            task["completed_at"] = datetime.now(UTC)
            task["activity"].append(
                {
                    "type": "assessment_cancelled",
                    "at": task["completed_at"].isoformat(),
                    "message": "Assessment processing cancelled",
                }
            )
            self._save(task)
        except Exception as exc:
            logger.exception("Assessment %s failed", task_id_str)
            task["status"] = "failed"
            task["error"] = str(exc)
            task["completed_at"] = datetime.now(UTC)
            task["activity"].append(
                {
                    "type": "assessment_failed",
                    "at": task["completed_at"].isoformat(),
                    "message": type(exc).__name__,
                }
            )
            self._save(task)

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
                    "at": datetime.now(UTC).isoformat(),
                    "message": "History indexing unavailable in current runtime",
                }
            )
            self._save(self._tasks[task_id])

    def _record(
        self,
        task_id: str,
        *,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if task is None:
            task = self._store.get(task_id)
            if task is not None:
                self._tasks[task_id] = task
        if task is None:
            raise TaskNotFoundError(task_id)
        if tenant_id is not None and task.get("tenant_id", "default") != tenant_id:
            raise TaskNotFoundError(task_id)
        return task

    def get(
        self, task_id: str, *, tenant_id: str | None = None
    ) -> AssessmentTaskResult:
        task = self._record(task_id, tenant_id=tenant_id)
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
            task_contract=task["task_contract"],
            plan_artifact=task.get("plan_artifact"),
            evaluation=task.get("evaluation"),
        )

    def list(
        self,
        *,
        statuses: set[str] | None = None,
        assignee: str | None = None,
        limit: int = 50,
        offset: int = 0,
        tenant_id: str | None = None,
    ) -> list[AssessmentTaskResult]:
        tasks = [
            task
            for task in self._store.list(tenant_id=tenant_id)
            if (not statuses or task.get("status") in statuses)
            and (not assignee or task.get("assignee") == assignee)
        ]
        tasks.sort(
            key=lambda task: task.get("created_at") or datetime.min,
            reverse=True,
        )
        return [
            self.get(str(task["task_id"]), tenant_id=tenant_id)
            for task in tasks[offset : offset + limit]
        ]

    async def wait_for_terminal(
        self,
        task_id: str,
        timeout_seconds: int,
        *,
        tenant_id: str | None = None,
    ) -> AssessmentTaskResult:
        async def poll() -> AssessmentTaskResult:
            while True:
                result = self.get(task_id, tenant_id=tenant_id)
                if result.status in TERMINAL_STATUSES:
                    return result
                await asyncio.sleep(0.05)

        return await asyncio.wait_for(poll(), timeout=timeout_seconds)

    def activity(
        self, task_id: str, *, tenant_id: str | None = None
    ) -> list[dict[str, Any]]:
        return list(self._record(task_id, tenant_id=tenant_id).get("activity", []))

    def add_comment(
        self,
        task_id: str,
        content: str,
        user_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        task = self._record(task_id, tenant_id=tenant_id)
        now = datetime.now(UTC)
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
        self._save(task)

    def review(
        self,
        task_id: str,
        *,
        action: str,
        comment: str | None,
        assignee: str | None,
        actor_id: int | None = None,
        actor_name: str | None = None,
        tenant_id: str | None = None,
    ) -> str:
        task = self._record(task_id, tenant_id=tenant_id)
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
        if action in {"approve", "reject"} and actor_id is not None:
            if actor_id == task.get("submitted_by_id"):
                raise InvalidTaskStateError(
                    "Assessment submitter cannot review own output"
                )
        new_status = status_by_action.get(action, current_status)
        task["status"] = new_status
        if assignee:
            task["assignee"] = assignee
        now = datetime.now(UTC)
        task["activity"].append(
            {
                "type": "review_action",
                "action": action,
                "at": now.isoformat(),
                "comment": comment,
                "assignee": assignee,
                "actor_id": actor_id,
                "actor": actor_name,
            }
        )
        if comment:
            task["comments"].append(
                {"content": comment, "at": now.isoformat(), "action": action}
            )
        self._save(task)
        return new_status

    def cancel(
        self,
        task_id: str,
        *,
        actor: str,
        tenant_id: str | None = None,
    ) -> str:
        task = self._record(task_id, tenant_id=tenant_id)
        if task["status"] in TERMINAL_STATUSES:
            raise InvalidTaskStateError(
                f"Cannot cancel task in status {task['status']}"
            )
        active = self._active.get(task_id)
        if active:
            active.cancel()
        else:
            task["status"] = "cancelled"
            task["completed_at"] = datetime.now(UTC)
            task["activity"].append(
                {
                    "type": "assessment_cancelled",
                    "at": task["completed_at"].isoformat(),
                    "actor": actor,
                }
            )
            self._save(task)
        return "cancelled"

    async def resume_incomplete(self) -> int:
        resumed = 0
        for stored in iter_incomplete(self._store):
            task_id_str = str(stored["task_id"])
            if task_id_str in self._active:
                continue
            execution = stored.get("execution") or {}
            documents = execution.get("parsed_documents") or []
            if not execution.get("resumable") or not documents:
                stored["status"] = "interrupted"
                self._save(stored)
                continue
            self._tasks[task_id_str] = stored
            parsed_documents = [
                ParsedDocument.model_validate(item) for item in documents
            ]
            active = asyncio.create_task(
                self._run(
                    task_id_str,
                    UUID(task_id_str),
                    parsed_documents,
                    execution.get("scenario_id"),
                    execution.get("project_id"),
                    execution.get("phase", "auto"),
                    execution.get("skill_id"),
                    bool(execution.get("collaborative_mode", True)),
                    run_assessment,
                )
            )
            self._active[task_id_str] = active
            active.add_done_callback(
                lambda _task, key=task_id_str: self._active.pop(key, None)
            )
            resumed += 1
        return resumed

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
        existing["updated_at"] = datetime.now(UTC)
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
        self._save(task)
        return RemediationTracking.model_validate(existing)


assessment_service = AssessmentService()
