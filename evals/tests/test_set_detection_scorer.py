from app.models.assessment import (
    AssessmentReport,
    ComplianceGap,
    RiskItem,
    SourceCitation,
)
from evals.models import (
    ComplianceGapTruth,
    EvalCase,
    EvalGroundTruth,
    EvalInput,
    RiskTruth,
)
from evals.scoring.scorers.set_detection import record_from_report, score_records


def _case() -> EvalCase:
    return EvalCase(
        case_id="case-1",
        dataset_id="ssdlc_synthetic_v1",
        phase="design",
        skill_id="ssdlc-design",
        inputs=[EvalInput(path="design.md", type="markdown")],
        ground_truth=EvalGroundTruth(
            risk_items=[
                RiskTruth(
                    id="R1",
                    title="Unsigned identity",
                    severity="high",
                    description="The client controls identity.",
                    match_terms=["client", "identity"],
                    evidence_locators=["DES-01"],
                )
            ],
            compliance_gaps=[
                ComplianceGapTruth(
                    id="G1",
                    framework="generic-ssdlc",
                    control_or_clause="GEN-IAM-01",
                    gap_description="Authentication is missing.",
                    match_terms=["authentication", "missing"],
                    evidence_locators=["DES-01"],
                )
            ],
        ),
    )


def test_scorer_reports_detection_and_fidelity_failures_separately():
    report = AssessmentReport(
        task_id="task",
        phase="design",
        status="completed",
        summary="test",
        risk_items=[
            RiskItem(
                id="R1",
                title="Unsigned identity",
                severity="medium",
                description="The client controls identity.",
                citation_ids=["C1"],
            ),
            RiskItem(
                id="EXTRA",
                title="Unsupported extra risk",
                severity="low",
            ),
        ],
        compliance_gaps=[
            ComplianceGap(
                id="G1",
                framework="other-framework",
                control_or_clause="OTHER-1",
                gap_description="Authentication is missing.",
                citation_ids=["C1"],
            )
        ],
        sources=[
            SourceCitation(
                id="C1",
                file="design.md",
                excerpt="unrelated evidence",
                locator="DES-99",
                source_kind="current_document",
            )
        ],
    )

    metrics = score_records([record_from_report(_case(), report, 0)])

    assert metrics["risk_detection"]["precision"] == 0.5
    assert metrics["risk_detection"]["recall"] == 1.0
    assert metrics["compliance_gap_detection"]["f1"] == 1.0
    assert metrics["severity_accuracy_on_matched"] == 0.0
    assert metrics["policy_mapping_accuracy_on_matched"] == 0.0
    assert metrics["evidence_locator_accuracy_on_matched"] == 0.0
    assert metrics["schema_validity"] == 1.0


def test_term_matching_is_one_to_one_when_prediction_ids_differ():
    report = AssessmentReport(
        task_id="task",
        phase="design",
        status="completed",
        summary="test",
        risk_items=[
            RiskItem(
                id="generated-risk",
                title="Client identity is trusted",
                severity="high",
                description="The client supplies identity without authentication.",
                source_ref="DES-01",
            )
        ],
        compliance_gaps=[],
    )

    record = record_from_report(_case(), report, 0)

    assert record.risk_matched == 1
    assert record.risk_predicted == 1
    assert record.risk_expected == 1
