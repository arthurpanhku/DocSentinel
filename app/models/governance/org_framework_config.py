import uuid
from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class OrgFrameworkConfig(SQLModel, table=True):
    __tablename__ = "org_framework_configs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    framework_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    default_review_mode: str = Field(default="ai_first", max_length=32)
    require_human_for_high_risk_ai: bool = True
    created_by_id: int | None = Field(default=None, foreign_key="user.id")
    updated_by_id: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
