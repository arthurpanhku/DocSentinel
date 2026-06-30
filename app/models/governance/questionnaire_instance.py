import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class QuestionnaireInstance(SQLModel, table=True):
    __tablename__ = "questionnaire_instances"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id", index=True, unique=True)
    generated_from_frameworks: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    generated_at: datetime = Field(default_factory=utcnow)
    is_complete: bool = False
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class QuestionInstance(SQLModel, table=True):
    __tablename__ = "question_instances"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    questionnaire_id: uuid.UUID = Field(
        foreign_key="questionnaire_instances.id",
        index=True,
    )
    question_key: str = Field(max_length=128)
    question_label: str = Field(sa_column=Column(Text, nullable=False))
    question_type: str = Field(max_length=32)
    options: list[str] | None = Field(default=None, sa_column=Column(JSON))
    group: str | None = Field(default=None, max_length=64)
    ask_when: str | None = Field(default=None, sa_column=Column(Text))
    sort_order: int = 0
    maps_to_control_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    answer: str | None = Field(default=None, sa_column=Column(Text))
    answered_at: datetime | None = None
