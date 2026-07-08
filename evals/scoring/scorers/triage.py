"""Binary SAST/DAST triage scoring for hard-key CWE datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.assessment import AssessmentReport, Vulnerability
from evals.models import EvalCase


@dataclass(frozen=True)
class TriageRecord:
    case_id: str
    phase: str
    skill_id: str
    cwe: str
    truth_label: str
    predicted_positive: bool
    repeat: int = 0

    @property
    def truth_positive(self) -> bool:
        return self.truth_label == "true_positive"

    @property
    def outcome(self) -> str:
        if self.truth_positive and self.predicted_positive:
            return "tp"
        if self.truth_positive and not self.predicted_positive:
            return "fn"
        if not self.truth_positive and self.predicted_positive:
            return "fp"
        return "tn"


def record_from_report(
    case: EvalCase,
    report: AssessmentReport,
    repeat: int,
) -> TriageRecord:
    """Build one binary triage record for an OWASP-style single-CWE case."""
    if not case.ground_truth.vulnerabilities:
        raise ValueError(f"Case has no vulnerability ground truth: {case.case_id}")
    truth = case.ground_truth.vulnerabilities[0]
    cwe = normalize_cwe(truth.cwe)
    return TriageRecord(
        case_id=case.case_id,
        phase=case.phase,
        skill_id=case.skill_id,
        cwe=cwe,
        truth_label=truth.label,
        predicted_positive=_has_matching_vulnerability(report.vulnerabilities, cwe),
        repeat=repeat,
    )


def score_records(records: list[TriageRecord]) -> dict[str, Any]:
    """Compute accuracy, precision, recall, F1, and false-positive rate."""
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for record in records:
        counts[record.outcome] += 1

    tp = counts["tp"]
    fp = counts["fp"]
    tn = counts["tn"]
    fn = counts["fn"]
    total = tp + fp + tn + fn
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    return {
        **counts,
        "total": total,
        "accuracy": _safe_div(tp + tn, total),
        "precision": precision,
        "recall": recall,
        "f1": _safe_div(2 * precision * recall, precision + recall),
        "false_positive_rate": _safe_div(fp, fp + tn),
    }


def normalize_cwe(value: object) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    return text if text.startswith("CWE-") else f"CWE-{text}"


def _has_matching_vulnerability(
    vulnerabilities: list[Vulnerability],
    expected_cwe: str,
) -> bool:
    for vuln in vulnerabilities:
        if vuln.status == "false_positive":
            continue
        if normalize_cwe(vuln.cwe_id) == expected_cwe:
            return True
    return False


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
