import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class SubAgentStatus(StrEnum):
    empty = "empty"
    draft = "draft"
    in_review = "in_review"
    changes_requested = "changes_requested"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


VALID_TRANSITIONS: set[tuple[str, str]] = {
    ("empty", "draft"),
    ("draft", "draft"),
    ("draft", "in_review"),
    ("in_review", "changes_requested"),
    ("in_review", "approved"),
    ("in_review", "rejected"),
    ("changes_requested", "draft"),
    ("approved", "archived"),
    ("rejected", "archived"),
    ("draft", "archived"),
    ("empty", "archived"),
}

COMMENT_REQUIRED: set[str] = {"changes_requested", "rejected"}

STATUS_ROLE_MAP: dict[str, set[str]] = {
    "in_review": {"security_reviewer", "security_approver", "admin"},
    "approved": {"security_approver", "admin"},
    "rejected": {"security_approver", "admin"},
    "changes_requested": {"security_reviewer", "security_approver", "admin"},
    "draft": {"client", "admin"},
    "archived": {"admin"},
    "empty": set(),
}


class SubAgentRun(SQLModel, table=True):
    __tablename__ = "sub_agent_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id", index=True)
    gate: str = Field(max_length=16)
    sub_agent_key: str = Field(max_length=64)
    status: str = Field(default=SubAgentStatus.empty.value, index=True, max_length=32)
    actor_id: int | None = Field(default=None, foreign_key="user.id")
    comment: str | None = Field(default=None, sa_column=Column(Text))
    run_output: dict | None = Field(default=None, sa_column=Column(JSON))
    last_transitioned_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def can_transition_to(self, new_status: str) -> bool:
        return (self.status, new_status) in VALID_TRANSITIONS
