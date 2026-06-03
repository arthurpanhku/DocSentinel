"""
Assessment report and task models.
Aligned with docs/schemas/assessment-report.json and
docs/03-assessment-report-and-skill-contract.md.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RiskItem(BaseModel):
    id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str | None = None
    source_ref: str | None = None
    category: str | None = None


class ComplianceGap(BaseModel):
    id: str
    control_or_clause: str
    gap_description: str
    evidence_suggestion: str | None = None
    framework: str | None = None


class Remediation(BaseModel):
    id: str
    action: str
    priority: Literal["low", "medium", "high"] | None = None
    related_risk_ids: list[str] = Field(default_factory=list)
    related_gap_ids: list[str] = Field(default_factory=list)


class SourceCitation(BaseModel):
    id: str
    file: str
    page: int | None = None
    paragraph_id: str | None = None
    excerpt: str
    evidence_link: str | None = None
    score: float | None = None


class ReportMetadata(BaseModel):
    scenario_id: str | None = None
    project_id: str | None = None
    ssdlc_stage: str | None = None
    ssdlc_phase: str | None = None
    skill_id: str | None = None
    model_used: str | None = None
    completed_at: datetime | None = None


class AssessmentReport(BaseModel):
    version: str = "1.0"
    task_id: str
    phase: str | None = None
    status: Literal["completed", "partial", "failed"]
    summary: str
    risk_items: list[RiskItem] = Field(default_factory=list)
    compliance_gaps: list[ComplianceGap] = Field(default_factory=list)
    remediations: list[Remediation] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[SourceCitation] = Field(default_factory=list)
    metadata: ReportMetadata | None = None
    format: Literal["json", "markdown"] = "json"


class AssessmentTaskCreated(BaseModel):
    task_id: UUID
    status: Literal["accepted", "queued"]
    message: str | None = None


class AssessmentTaskResult(BaseModel):
    task_id: UUID
    status: Literal[
        "pending",
        "running",
        "review_pending",
        "approved",
        "rejected",
        "escalated",
        "completed",
        "failed",
    ]
    report: AssessmentReport | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    version: int = 1
    assignee: str | None = None
    comments: list[dict] = Field(default_factory=list)
