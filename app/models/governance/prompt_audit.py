import uuid
from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class PromptAuditLog(SQLModel, table=True):
    __tablename__ = "prompt_audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sub_agent_run_id: uuid.UUID | None = Field(default=None, index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    project_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="projects.id",
        index=True,
    )
    message_id: uuid.UUID | None = Field(default=None, index=True)
    mvp_task: str | None = Field(default=None, index=True, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    prompt_digest: str = Field(max_length=64)
    response_digest: str = Field(max_length=64)
    token_count_in: int = 0
    token_count_out: int = 0
    pii_fields_redacted: list[str] | None = Field(default=None, sa_column=Column(JSON))
    safety: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow, index=True)
