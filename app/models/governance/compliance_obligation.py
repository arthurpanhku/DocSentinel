import uuid
from datetime import datetime

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class ComplianceObligation(SQLModel, table=True):
    __tablename__ = "compliance_obligations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id", index=True)
    framework_id: str = Field(index=True, max_length=64)
    framework_version: str = Field(default="0.0.0", max_length=32)
    applicability_rationale: str | None = Field(default=None, sa_column=Column(Text))
    mandatory: bool = False
    resolved_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)
