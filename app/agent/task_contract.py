"""Deterministic Task Contract, planning, and evaluation helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from app.models.agent_execution import (
    AgentTaskContract,
    EvaluationArtifact,
    EvaluationCheck,
    PlanArtifact,
    PlanStep,
    TaskInputReference,
)
from app.models.assessment import AssessmentReport
from app.models.parser import ParsedDocument


def build_task_contract(
    *,
    task_id: UUID,
    parsed_documents: list[ParsedDocument],
    phase: str | None,
    created_at: datetime | None = None,
) -> AgentTaskContract:
    """Create the bounded contract shared by REST, MCP, and A2A assessments."""
    inputs = tuple(_input_reference(document) for document in parsed_documents)
    normalized_phase = phase or "auto"
    risk_tier = (
        "high"
        if normalized_phase in {"deployment", "operations", "full_ssdlc"}
        else "medium"
    )
    return AgentTaskContract(
        task_id=task_id,
        created_at=created_at or datetime.now(UTC),
        goal=(
            "Assess the submitted documents for security, compliance, and "
            f"evidence gaps in the {normalized_phase} SSDLC phase."
        ),
        inputs=inputs,
        allowed_paths=tuple(item.uri for item in inputs),
        allowed_tools=(
            "document.read",
            "knowledge_base.search",
            "llm.generate",
            "evidence.verify",
        ),
        expected_outputs=("assessment_report.v2", "evaluation_artifact.v1"),
        success_criteria=(
            "The report satisfies the AssessmentReport schema.",
            "Every supported citation resolves to an allowed input or trusted source.",
            "Threat evidence is evaluated independently from report drafting.",
            "The result remains pending until the configured human review completes.",
        ),
        risk_tier=risk_tier,
        # Plan-first enforcement is a later M1 policy slice. Until then every
        # task remains under the existing mandatory human-review boundary.
        approval_mode="human_review",
        retry_limit=2,
        escalation_owner="security_reviewer",
    )


def build_plan_artifact(
    contract: AgentTaskContract,
    *,
    skill_id: str | None,
) -> PlanArtifact:
    """Produce a visible plan without invoking tools or reading document content."""
    return PlanArtifact(
        task_id=contract.task_id,
        created_at=datetime.now(UTC),
        skill_id=skill_id,
        steps=(
            PlanStep(
                id="plan-1",
                phase="plan",
                action="Validate the task contract and select the assessment skill.",
                inputs=("agent_task_contract.v1",),
                outputs=("plan_artifact.v1",),
                success_check="Contract fields are valid and all inputs are in scope.",
            ),
            PlanStep(
                id="act-1",
                phase="act",
                action="Build bounded document context and retrieve policy evidence.",
                inputs=contract.allowed_paths,
                outputs=("document_context", "policy_context", "history_context"),
                success_check=(
                    "Only allowed inputs and read-only retrieval tools are used."
                ),
            ),
            PlanStep(
                id="act-2",
                phase="act",
                action="Draft and independently review the structured assessment.",
                inputs=("document_context", "policy_context", "history_context"),
                outputs=("assessment_report.v2",),
                success_check="The reviewer emits a schema-valid assessment report.",
            ),
            PlanStep(
                id="evaluate-1",
                phase="evaluate",
                action="Verify evidence and apply deterministic success checks.",
                inputs=("assessment_report.v2",),
                outputs=("evaluation_artifact.v1",),
                success_check=(
                    "Required checks pass or the result is marked for review."
                ),
            ),
        ),
    )


def evaluate_assessment_report(
    report: AssessmentReport,
    contract: AgentTaskContract,
) -> EvaluationArtifact:
    """Evaluate generated output with deterministic checks outside the drafter."""
    schema_valid = True
    schema_details = "AssessmentReport schema validation passed."
    try:
        AssessmentReport.model_validate(report.model_dump())
    except ValueError as exc:
        schema_valid = False
        schema_details = f"AssessmentReport schema validation failed: {exc}"

    finding_count = len(report.risk_items) + len(report.compliance_gaps)
    evidence_present = finding_count == 0 or bool(report.sources)
    threats = report.threat_model.threats if report.threat_model else []
    threats_verified = all(threat.verification is not None for threat in threats)

    checks = (
        EvaluationCheck(
            name="schema_valid",
            passed=schema_valid,
            details=schema_details,
        ),
        EvaluationCheck(
            name="task_identity_matches",
            passed=report.task_id == str(contract.task_id),
            details="Report task ID must match the immutable task contract.",
        ),
        EvaluationCheck(
            name="required_output_present",
            passed=bool(report.summary.strip()) and report.status != "failed",
            details="A non-empty, non-failed assessment report is required.",
        ),
        EvaluationCheck(
            name="finding_evidence_present",
            passed=evidence_present,
            required=False,
            details="Findings should include at least one structured source citation.",
        ),
        EvaluationCheck(
            name="threat_evidence_verified",
            passed=threats_verified,
            details="Every generated threat must pass through the evidence critic.",
        ),
    )
    required_failed = any(not check.passed for check in checks if check.required)
    advisory_failed = any(not check.passed for check in checks if not check.required)
    if required_failed:
        outcome = "failed"
    elif advisory_failed:
        outcome = "needs_review"
    else:
        outcome = "passed"
    return EvaluationArtifact(
        task_id=contract.task_id,
        created_at=datetime.now(UTC),
        outcome=outcome,
        checks=checks,
    )


def _input_reference(document: ParsedDocument) -> TaskInputReference:
    content = (
        document.content if isinstance(document.content, str) else str(document.content)
    )
    digest = document.metadata.file_hash or sha256(content.encode("utf-8")).hexdigest()
    return TaskInputReference(
        uri=f"document://{digest}",
        filename=document.metadata.filename,
        media_type=document.metadata.type,
        sha256=digest,
    )
