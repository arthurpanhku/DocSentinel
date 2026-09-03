"""Durable assessment task record.

The lifecycle payload is intentionally stored as versioned JSON so task-contract,
plan, evaluation, review, and remediation schemas can evolve independently.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class AssessmentTaskRecord(SQLModel, table=True):
    __tablename__ = "assessment_tasks"

    task_id: UUID = Field(primary_key=True)
    tenant_id: str = Field(default="default", index=True, max_length=128)
    submitted_by_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    idempotency_key: str | None = Field(default=None, index=True, max_length=255)
    status: str = Field(index=True, max_length=32)
    phase: str = Field(default="auto", index=True, max_length=32)
    source: str = Field(default="rest", index=True, max_length=32)
    data: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(index=True)
    updated_at: datetime = Field(index=True)
