import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.governance.common import utcnow


class KnowledgeBaseType(StrEnum):
    user_side = "user_side"
    security_side = "security_side"


class Language(StrEnum):
    zh = "zh"
    en = "en"


class PolicyDocument(SQLModel, table=True):
    __tablename__ = "policy_documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=512)
    language: str = Field(default=Language.en.value, max_length=8)
    doc_type: str | None = Field(default=None, max_length=128)
    file_path: str = Field(max_length=1024)
    version: str | None = Field(default=None, max_length=64)
    is_active: bool = True
    uploaded_by_id: int | None = Field(default=None, foreign_key="user.id")
    kb_type: str = Field(default=KnowledgeBaseType.user_side.value, max_length=32)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class PolicyEmbedding(SQLModel, table=True):
    __tablename__ = "policy_embeddings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="policy_documents.id", index=True)
    chunk_text: str = Field(sa_column=Column(Text, nullable=False))
    embedding: list[float] = Field(sa_column=Column(JSON, nullable=False))
    chunk_index: int = 0
    language: str = Field(default=Language.en.value, max_length=8)
