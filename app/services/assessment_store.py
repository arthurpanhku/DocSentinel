"""Persistence boundary for assessment lifecycle records."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, SQLModel, col, delete, select

from app.models.assessment_task import AssessmentTaskRecord


class AssessmentTaskStore(Protocol):
    def save(self, task: dict) -> None: ...

    def get(self, task_id: str) -> dict | None: ...

    def list(self, *, tenant_id: str | None = None) -> list[dict]: ...

    def find_idempotent(self, tenant_id: str, idempotency_key: str) -> dict | None: ...

    def clear(self) -> None: ...


class MemoryAssessmentTaskStore:
    def __init__(self) -> None:
        self.tasks: dict[str, dict] = {}

    def save(self, task: dict) -> None:
        self.tasks[str(task["task_id"])] = task

    def get(self, task_id: str) -> dict | None:
        return self.tasks.get(task_id)

    def list(self, *, tenant_id: str | None = None) -> list[dict]:
        return [
            task
            for task in self.tasks.values()
            if tenant_id is None or task.get("tenant_id", "default") == tenant_id
        ]

    def find_idempotent(self, tenant_id: str, idempotency_key: str) -> dict | None:
        return next(
            (
                task
                for task in self.tasks.values()
                if task.get("tenant_id", "default") == tenant_id
                and task.get("idempotency_key") == idempotency_key
            ),
            None,
        )

    def clear(self) -> None:
        self.tasks.clear()


class SqlAssessmentTaskStore:
    def __init__(self, engine, *, create_tables: bool = False) -> None:
        self.engine = engine
        if create_tables:
            SQLModel.metadata.create_all(
                engine, tables=[AssessmentTaskRecord.__table__]
            )

    @staticmethod
    def _payload(record: AssessmentTaskRecord) -> dict:
        return dict(record.data)

    def save(self, task: dict) -> None:
        task_id = task["task_id"]
        with Session(self.engine) as session:
            record = session.get(AssessmentTaskRecord, task_id)
            values = {
                "tenant_id": task.get("tenant_id", "default"),
                "submitted_by_id": task.get("submitted_by_id"),
                "idempotency_key": task.get("idempotency_key"),
                "status": task["status"],
                "phase": task.get("phase", "auto"),
                "source": task.get("source", "rest"),
                "data": jsonable_encoder(task),
                "created_at": task["created_at"],
                "updated_at": task.get("updated_at", task["created_at"]),
            }
            if record is None:
                record = AssessmentTaskRecord(task_id=task_id, **values)
            else:
                for key, value in values.items():
                    setattr(record, key, value)
            session.add(record)
            session.commit()

    def get(self, task_id: str) -> dict | None:
        with Session(self.engine) as session:
            try:
                record = session.get(AssessmentTaskRecord, UUID(str(task_id)))
            except (TypeError, ValueError):
                return None
            return self._payload(record) if record else None

    def list(self, *, tenant_id: str | None = None) -> list[dict]:
        with Session(self.engine) as session:
            statement = select(AssessmentTaskRecord)
            if tenant_id is not None:
                statement = statement.where(AssessmentTaskRecord.tenant_id == tenant_id)
            statement = statement.order_by(col(AssessmentTaskRecord.created_at).desc())
            return [self._payload(record) for record in session.exec(statement).all()]

    def find_idempotent(self, tenant_id: str, idempotency_key: str) -> dict | None:
        with Session(self.engine) as session:
            record = session.exec(
                select(AssessmentTaskRecord).where(
                    AssessmentTaskRecord.tenant_id == tenant_id,
                    AssessmentTaskRecord.idempotency_key == idempotency_key,
                )
            ).first()
            return self._payload(record) if record else None

    def clear(self) -> None:
        with Session(self.engine) as session:
            session.exec(delete(AssessmentTaskRecord))
            session.commit()


def iter_incomplete(store: AssessmentTaskStore) -> Iterable[dict]:
    return (
        task
        for task in store.list()
        if task.get("status") in {"pending", "running", "interrupted"}
    )
