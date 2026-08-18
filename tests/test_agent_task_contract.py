"""Task Contract and Plan–Act–Evaluate artifact tests."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.agent.task_contract import (
    build_plan_artifact,
    build_task_contract,
    evaluate_assessment_report,
)
from app.models.assessment import AssessmentReport, RiskItem
from app.models.parser import ParsedDocument, ParsedDocumentMetadata


def _document() -> ParsedDocument:
    return ParsedDocument(
        metadata=ParsedDocumentMetadata(
            filename="design.md",
            type="md",
            file_hash="a" * 64,
        ),
        content="# Design\nThe API uses OIDC.",
    )


def test_task_contract_is_versioned_bounded_and_immutable():
    task_id = uuid4()
    contract = build_task_contract(
        task_id=task_id,
        parsed_documents=[_document()],
        phase="design",
    )

    assert contract.version == "1.0"
    assert contract.task_id == task_id
    assert contract.inputs[0].sha256 == "a" * 64
    assert contract.allowed_paths == (f"document://{'a' * 64}",)
    assert contract.risk_tier == "medium"
    assert contract.approval_mode == "human_review"
    assert contract.retry_limit == 2
    assert contract.escalation_owner == "security_reviewer"

    with pytest.raises(ValidationError):
        contract.goal = "Replace the approved goal"


def test_plan_exposes_plan_act_evaluate_order_without_mutating_contract():
    contract = build_task_contract(
        task_id=uuid4(),
        parsed_documents=[_document()],
        phase="design",
    )
    plan = build_plan_artifact(contract, skill_id="secure-design-review")

    assert plan.mode == "read_only"
    assert tuple(step.phase for step in plan.steps) == (
        "plan",
        "act",
        "act",
        "evaluate",
    )
    assert plan.steps[1].inputs == contract.allowed_paths

    with pytest.raises(ValidationError):
        plan.steps[0].action = "Skip planning"


def test_evaluation_is_independent_and_flags_findings_without_evidence():
    task_id = uuid4()
    contract = build_task_contract(
        task_id=task_id,
        parsed_documents=[_document()],
        phase="design",
    )
    report = AssessmentReport(
        task_id=str(task_id),
        status="completed",
        summary="One risk needs review.",
        risk_items=[
            RiskItem(
                id="R1",
                title="Missing authorization detail",
                severity="high",
            )
        ],
    )

    evaluation = evaluate_assessment_report(report, contract)

    assert evaluation.evaluator == "deterministic_policy"
    assert evaluation.outcome == "needs_review"
    evidence_check = next(
        check for check in evaluation.checks if check.name == "finding_evidence_present"
    )
    assert evidence_check.passed is False
    assert evidence_check.required is False
