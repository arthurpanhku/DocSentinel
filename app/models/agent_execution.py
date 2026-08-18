"""Versioned, immutable artifacts for bounded agent execution."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _ImmutableArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TaskInputReference(_ImmutableArtifact):
    uri: str
    filename: str
    media_type: str
    sha256: str


class AgentTaskContract(_ImmutableArtifact):
    version: Literal["1.0"] = "1.0"
    task_id: UUID
    created_at: datetime
    goal: str
    inputs: tuple[TaskInputReference, ...] = Field(min_length=1)
    allowed_paths: tuple[str, ...] = Field(min_length=1)
    allowed_tools: tuple[str, ...] = Field(min_length=1)
    expected_outputs: tuple[str, ...] = Field(min_length=1)
    success_criteria: tuple[str, ...] = Field(min_length=1)
    risk_tier: Literal["low", "medium", "high", "critical"]
    approval_mode: Literal["human_review", "plan_first"]
    retry_limit: int = Field(ge=0, le=5)
    escalation_owner: str


class PlanStep(_ImmutableArtifact):
    id: str
    phase: Literal["plan", "act", "evaluate"]
    action: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    success_check: str


class PlanArtifact(_ImmutableArtifact):
    version: Literal["1.0"] = "1.0"
    task_id: UUID
    contract_version: Literal["1.0"] = "1.0"
    created_at: datetime
    mode: Literal["read_only"] = "read_only"
    skill_id: str | None = None
    steps: tuple[PlanStep, ...] = Field(min_length=1)


class EvaluationCheck(_ImmutableArtifact):
    name: str
    passed: bool
    required: bool = True
    details: str


class EvaluationArtifact(_ImmutableArtifact):
    version: Literal["1.0"] = "1.0"
    task_id: UUID
    created_at: datetime
    evaluator: Literal["deterministic_policy"] = "deterministic_policy"
    outcome: Literal["passed", "needs_review", "failed"]
    checks: tuple[EvaluationCheck, ...] = Field(min_length=1)
