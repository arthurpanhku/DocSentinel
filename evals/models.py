"""Shared models for the DocSentinel evaluation harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

Phase = Literal[
    "auto",
    "requirements",
    "design",
    "development",
    "testing",
    "deployment",
    "operations",
    "full_ssdlc",
]
TruthLabel = Literal["true_positive", "false_positive"]


class EvalInput(BaseModel):
    """One input artifact referenced by an evaluation case."""

    path: str
    type: str


class VulnerabilityTruth(BaseModel):
    """Ground truth for one SAST/DAST triage item."""

    cwe: str
    label: TruthLabel
    category: str | None = None
    test_name: str | None = None


class EvalGroundTruth(BaseModel):
    """Ground-truth item sets, aligned to the assessment report schema."""

    threats: list[dict[str, Any]] = Field(default_factory=list)
    risk_items: list[dict[str, Any]] = Field(default_factory=list)
    compliance_gaps: list[dict[str, Any]] = Field(default_factory=list)
    vulnerabilities: list[VulnerabilityTruth] = Field(default_factory=list)


class EvalCase(BaseModel):
    """Normalized dataset case consumed by runners and scorers."""

    case_id: str
    dataset_id: str
    phase: Phase
    skill_id: str
    inputs: list[EvalInput]
    ground_truth: EvalGroundTruth
    meta: dict[str, Any] = Field(default_factory=dict)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")


class RunConfig(BaseModel):
    """Execution settings for one evaluation run."""

    run_id: str = "local"
    dataset_id: str = "owasp_benchmark"
    provider: str = "ollama-local"
    model_id: str = "llama2"
    temperature: float = 0.0
    repeats: int = Field(default=3, ge=1)
    timeout_seconds: int = Field(default=300, ge=1)
    collaborative: bool = True
    phase: Phase = "testing"
    skill_id: str = "ssdlc-testing"
    limit: int | None = Field(default=None, ge=1)

