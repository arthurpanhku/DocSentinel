from app.models.assessment import AssessmentReport, Vulnerability
from evals.models import EvalCase, EvalGroundTruth, EvalInput, VulnerabilityTruth
from evals.scoring.scorers.triage import record_from_report, score_records


def _case(case_id: str, cwe: str, label: str) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        dataset_id="owasp_benchmark",
        phase="testing",
        skill_id="ssdlc-testing",
        inputs=[EvalInput(path=f"{case_id}.java", type="java")],
        ground_truth=EvalGroundTruth(
            vulnerabilities=[VulnerabilityTruth(cwe=cwe, label=label)]
        ),
    )


def _report(*vulnerabilities: Vulnerability) -> AssessmentReport:
    return AssessmentReport(
        task_id="task",
        phase="testing",
        status="completed",
        summary="test",
        vulnerabilities=list(vulnerabilities),
    )


def _vuln(cwe: str) -> Vulnerability:
    return Vulnerability(
        id="v1",
        title="Finding",
        severity="high",
        cwe_id=cwe,
    )


def test_triage_scorer_computes_binary_metrics():
    records = [
        record_from_report(
            _case("tp", "CWE-89", "true_positive"),
            _report(_vuln("89")),
            0,
        ),
        record_from_report(
            _case("fp", "CWE-22", "false_positive"),
            _report(_vuln("22")),
            0,
        ),
        record_from_report(_case("fn", "CWE-78", "true_positive"), _report(), 0),
        record_from_report(_case("tn", "CWE-79", "false_positive"), _report(), 0),
    ]

    metrics = score_records(records)

    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert metrics["tn"] == 1
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["false_positive_rate"] == 0.5
