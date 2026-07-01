import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class GateStatus(StrEnum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    changes_requested = "changes_requested"
    rejected = "rejected"
    rework = "rework"
    completed = "completed"


class ReviewStatus(StrEnum):
    pending_review = "pending_review"
    accepted = "accepted"
    rejected = "rejected"
    needs_clarification = "needs_clarification"


class EvidenceType(StrEnum):
    text = "text"
    image = "image"
    link = "link"


GATE_STATUS_TRANSITIONS: dict[tuple[str, str], tuple[str, ...]] = {
    ("draft", "pending"): ("client", "security_reviewer", "admin"),
    ("rework", "pending"): ("client", "security_reviewer", "admin"),
    ("pending", "approved"): ("security_reviewer", "security_approver", "admin"),
    ("pending", "changes_requested"): (
        "security_reviewer",
        "security_approver",
        "admin",
    ),
    ("pending", "rejected"): ("security_reviewer", "security_approver", "admin"),
    ("changes_requested", "rework"): ("client", "admin"),
    ("approved", "completed"): ("security_approver", "admin"),
}

COMMENT_REQUIRED_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("pending", "changes_requested"),
        ("pending", "rejected"),
    }
)


class GateSubmission(SQLModel, table=True):
    __tablename__ = "gate_submissions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id", index=True)
    gate_number: int = Field(index=True)
    status: str = Field(default=GateStatus.draft.value, index=True, max_length=32)
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by_id: int | None = Field(default=None, foreign_key="user.id")
    intake_payload: dict | None = Field(default=None, sa_column=Column(JSON))
    reviewer_comments: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class RequirementRow(SQLModel, table=True):
    __tablename__ = "requirement_rows"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    gate_submission_id: uuid.UUID = Field(
        foreign_key="gate_submissions.id",
        index=True,
    )
    requirement_id: str | None = Field(default=None, max_length=128)
    domain: str | None = Field(default=None, max_length=128)
    requirement_text: str = Field(sa_column=Column(Text, nullable=False))
    organization_guidance: str | None = Field(default=None, sa_column=Column(Text))
    applicability: str | None = Field(default=None, max_length=64)
    risk_level: str | None = Field(default=None, max_length=32)
    review_status: str = Field(
        default=ReviewStatus.pending_review.value,
        index=True,
        max_length=32,
    )
    ai_confidence: float | None = None
    reviewer_notes: str | None = Field(default=None, sa_column=Column(Text))
    review_history: list[dict] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    scd_extras: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class EvidenceItem(SQLModel, table=True):
    __tablename__ = "evidence_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    requirement_row_id: uuid.UUID = Field(
        foreign_key="requirement_rows.id",
        index=True,
    )
    evidence_type: str = Field(max_length=16)
    content: str | None = Field(default=None, sa_column=Column(Text))
    file_path: str | None = Field(default=None, max_length=1024)
    url: str | None = Field(default=None, max_length=2048)
    ai_analysis: dict | None = Field(default=None, sa_column=Column(JSON))
    submitted_at: datetime = Field(default_factory=utcnow)
