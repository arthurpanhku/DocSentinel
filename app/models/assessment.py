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
    phase: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    citation_ids: list[str] = Field(default_factory=list)


class ComplianceGap(BaseModel):
    id: str
    control_or_clause: str
    gap_description: str
    evidence_suggestion: str | None = None
    framework: str | None = None
    phase: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    citation_ids: list[str] = Field(default_factory=list)


class Remediation(BaseModel):
    id: str
    action: str
    priority: Literal["low", "medium", "high", "critical"] | None = None
    related_risk_ids: list[str] = Field(default_factory=list)
    related_gap_ids: list[str] = Field(default_factory=list)
    related_vuln_ids: list[str] = Field(default_factory=list)
    related_threat_ids: list[str] = Field(default_factory=list)
    external_ticket: str | None = None
    phase: str | None = None


class DreadScore(BaseModel):
    damage: int | None = Field(default=None, ge=1, le=10)
    reproducibility: int | None = Field(default=None, ge=1, le=10)
    exploitability: int | None = Field(default=None, ge=1, le=10)
    affected_users: int | None = Field(default=None, ge=1, le=10)
    discoverability: int | None = Field(default=None, ge=1, le=10)
    total: float | None = None


class EvidenceVerification(BaseModel):
    status: Literal["supported", "contradicted", "insufficient_evidence"]
    support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    requires_human_review: Literal[True] = True


class Threat(BaseModel):
    id: str
    category: Literal[
        "Spoofing",
        "Tampering",
        "Repudiation",
        "InformationDisclosure",
        "DenialOfService",
        "ElevationOfPrivilege",
    ]
    description: str
    affected_component: str | None = None
    dread_score: DreadScore | None = None
    mitigations: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    citation_ids: list[str] = Field(default_factory=list)
    verification: EvidenceVerification | None = None


class EvidenceCriticSummary(BaseModel):
    status: Literal["completed", "fallback"]
    verifier: str
    supported: int = 0
    contradicted: int = 0
    insufficient_evidence: int = 0
    total: int = 0


class ThreatModel(BaseModel):
    methodology: Literal["STRIDE", "DREAD", "STRIDE_DREAD"] | None = None
    threats: list[Threat] = Field(default_factory=list)
    verification_summary: EvidenceCriticSummary | None = None


class Vulnerability(BaseModel):
    id: str
    title: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    source_tool: str | None = None
    cwe_id: str | None = None
    cvss_score: float | None = None
    location: str | None = None
    description: str | None = None
    remediation: str | None = None
    status: Literal[
        "open",
        "in_progress",
        "fixed",
        "accepted",
        "false_positive",
    ] = "open"
    linked_threat_id: str | None = None


class CrossPhaseRef(BaseModel):
    source_phase: str
    source_id: str
    target_phase: str
    target_id: str
    relationship: str


class SourceCitation(BaseModel):
    id: str
    file: str
    page: int | None = None
    paragraph_id: str | None = None
    excerpt: str
    evidence_link: str | None = None
    score: float | None = None
    document_hash: str | None = None
    locator: str | None = None
    source_kind: Literal[
        "current_document",
        "policy",
        "history",
    ] = "policy"


class ReportMetadata(BaseModel):
    scenario_id: str | None = None
    project_id: str | None = None
    ssdlc_stage: str | None = None
    ssdlc_phase: str | None = None
    skill_id: str | None = None
    model_used: str | None = None
    completed_at: datetime | None = None


class AssessmentReport(BaseModel):
    version: str = "2.0"
    task_id: str
    phase: str | None = None
    status: Literal["completed", "partial", "failed"]
    summary: str
    risk_items: list[RiskItem] = Field(default_factory=list)
    compliance_gaps: list[ComplianceGap] = Field(default_factory=list)
    threat_model: ThreatModel | None = None
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    remediations: list[Remediation] = Field(default_factory=list)
    cross_phase_refs: list[CrossPhaseRef] = Field(default_factory=list)
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


class RemediationTracking(BaseModel):
    remediation_id: str
    status: Literal["open", "in_progress", "resolved", "verified", "closed"] = "open"
    owner: str | None = None
    due_at: datetime | None = None
    external_ticket: str | None = None
    notes: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class TrackedRemediation(BaseModel):
    remediation: Remediation
    tracking: RemediationTracking
