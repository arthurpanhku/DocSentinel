import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class ProjectStatus(StrEnum):
    draft = "draft"
    active = "active"
    completed = "completed"
    archived = "archived"


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text))
    business_owner: str | None = Field(default=None, max_length=255)
    owner_id: int | None = Field(default=None, foreign_key="user.id", index=True)

    risk_tier: str | None = Field(default=None, max_length=32)
    control_profile: str | None = Field(default=None, max_length=32)
    compliance_frameworks: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    review_mode: str | None = Field(default=None, max_length=32)
    framework_ids_locked: bool = False

    involves_ai_ml: bool | None = None
    ai_risk_class: str | None = Field(default=None, max_length=32)
    slsa_target_level: int | None = None

    status: str = Field(default=ProjectStatus.draft.value, index=True, max_length=32)
    system_type: str | None = Field(default=None, max_length=128)
    hosting_type: str | None = Field(default=None, max_length=128)
    data_classification: str | None = Field(default=None, max_length=128)
    risk_level: int | None = None
    organization: str | None = Field(default=None, max_length=255)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
