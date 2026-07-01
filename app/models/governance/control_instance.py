import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class ControlStatus(StrEnum):
    pending = "pending"
    evidence_submitted = "evidence_submitted"
    ai_reviewing = "ai_reviewing"
    ai_reviewed = "ai_reviewed"
    human_reviewing = "human_reviewing"
    approved = "approved"
    rejected = "rejected"
    needs_clarification = "needs_clarification"
    not_applicable = "not_applicable"


class ControlInstance(SQLModel, table=True):
    __tablename__ = "control_instances"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id", index=True)
    control_id: str = Field(index=True, max_length=64)
    framework_id: str = Field(index=True, max_length=64)
    framework_citation: str | None = Field(default=None, sa_column=Column(Text))
    title: str = Field(sa_column=Column(Text, nullable=False))
    normalized_requirement: str = Field(sa_column=Column(Text, nullable=False))
    expected_evidence: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    review_focus: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    is_applicable: bool = True
    applicability_rationale: str | None = Field(default=None, sa_column=Column(Text))
    is_mandatory: bool = True
    review_mode: str = Field(default="ai_first", max_length=32)
    status: str = Field(default=ControlStatus.pending.value, index=True, max_length=32)
    ai_score: str | None = Field(default=None, max_length=32)
    ai_rationale: str | None = Field(default=None, sa_column=Column(Text))
    ai_missing_evidence: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )
    ai_confidence: float | None = None
    ai_requires_human: bool | None = None
    ai_reviewed_at: datetime | None = None
    human_decision: str | None = Field(default=None, max_length=32)
    human_notes: str | None = Field(default=None, sa_column=Column(Text))
    human_reviewer_id: int | None = Field(default=None, foreign_key="user.id")
    human_reviewed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ControlEvidenceItem(SQLModel, table=True):
    __tablename__ = "control_evidence_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    control_instance_id: uuid.UUID = Field(
        foreign_key="control_instances.id",
        index=True,
    )
    evidence_type: str = Field(max_length=16)
    content: str | None = Field(default=None, sa_column=Column(Text))
    file_path: str | None = Field(default=None, max_length=512)
    url: str | None = Field(default=None, max_length=512)
    ai_analysis: dict | None = Field(default=None, sa_column=Column(JSON))
    submitted_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
