import uuid
from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class GovernanceAuditLog(SQLModel, table=True):
    __tablename__ = "governance_audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(index=True, max_length=128)
    resource_type: str | None = Field(default=None, max_length=128)
    resource_id: str | None = Field(default=None, index=True, max_length=128)
    details: dict | None = Field(default=None, sa_column=Column(JSON))
    ip_address: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow, index=True)
