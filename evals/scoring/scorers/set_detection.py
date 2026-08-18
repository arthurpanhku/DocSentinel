"""Deterministic set scoring for synthetic SSDLC risks and policy gaps."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from app.models.assessment import AssessmentReport
from evals.models import EvalCase

PredictedItem = TypeVar("PredictedItem")
ExpectedItem = TypeVar("ExpectedItem")


@dataclass(frozen=True)
class GoldenRecord:
    case_id: str
    phase: str
    skill_id: str
    repeat: int
    risk_expected: int
    risk_predicted: int
    risk_matched: int
    gap_expected: int
    gap_predicted: int
    gap_matched: int
    severity_total: int
    severity_correct: int
    policy_total: int
    policy_correct: int
    evidence_total: int
    evidence_correct: int
    matches: tuple[dict[str, Any], ...]


def record_from_report(
    case: EvalCase,
    report: AssessmentReport,
    repeat: int,
) -> GoldenRecord:
    """Match one structured report against a synthetic case's golden findings."""
    risk_matches = _match_items(
        report.risk_items,
        case.ground_truth.risk_items,
        predicted_id=lambda item: item.id,
        predicted_text=lambda item: f"{item.title} {item.description or ''}",
        expected_id=lambda item: item.id or "",
        expected_terms=lambda item: item.match_terms,
    )
    gap_matches = _match_items(
        report.compliance_gaps,
        case.ground_truth.compliance_gaps,
        predicted_id=lambda item: item.id,
        predicted_text=lambda item: (
            f"{item.framework or ''} {item.control_or_clause} {item.gap_description}"
        ),
        expected_id=lambda item: item.id or "",
        expected_terms=lambda item: item.match_terms,
    )
    citations = {source.id: source for source in report.sources}
    details: list[dict[str, Any]] = []
    severity_correct = 0
    evidence_correct = 0
    for predicted_index, expected_index, score in risk_matches:
        predicted = report.risk_items[predicted_index]
        expected = case.ground_truth.risk_items[expected_index]
        severity_match = predicted.severity == expected.severity
        evidence_match = _evidence_matches(
            predicted.source_ref,
            predicted.citation_ids,
            expected.evidence_locators,
            citations,
        )
        severity_correct += int(severity_match)
        evidence_correct += int(evidence_match)
        details.append(
            {
                "kind": "risk",
                "expected_id": expected.id,
                "predicted_id": predicted.id,
                "match_score": score,
                "severity_correct": severity_match,
                "evidence_correct": evidence_match,
            }
        )

    policy_correct = 0
    for predicted_index, expected_index, score in gap_matches:
        predicted = report.compliance_gaps[predicted_index]
        expected = case.ground_truth.compliance_gaps[expected_index]
        policy_match = _normalize(predicted.framework or "") == _normalize(
            expected.framework
        ) and _normalize(predicted.control_or_clause) == _normalize(
            expected.control_or_clause
        )
        evidence_match = _evidence_matches(
            None,
            predicted.citation_ids,
            expected.evidence_locators,
            citations,
        )
        policy_correct += int(policy_match)
        evidence_correct += int(evidence_match)
        details.append(
            {
                "kind": "compliance_gap",
                "expected_id": expected.id,
                "predicted_id": predicted.id,
                "match_score": score,
                "policy_correct": policy_match,
                "evidence_correct": evidence_match,
            }
        )

    return GoldenRecord(
        case_id=case.case_id,
        phase=case.phase,
        skill_id=case.skill_id,
        repeat=repeat,
        risk_expected=len(case.ground_truth.risk_items),
        risk_predicted=len(report.risk_items),
        risk_matched=len(risk_matches),
        gap_expected=len(case.ground_truth.compliance_gaps),
        gap_predicted=len(report.compliance_gaps),
        gap_matched=len(gap_matches),
        severity_total=len(risk_matches),
        severity_correct=severity_correct,
        policy_total=len(gap_matches),
        policy_correct=policy_correct,
        evidence_total=len(risk_matches) + len(gap_matches),
        evidence_correct=evidence_correct,
        matches=tuple(details),
    )


def score_records(records: list[GoldenRecord]) -> dict[str, Any]:
    """Compute micro-averaged finding and fidelity metrics."""
    risk = _detection_metrics(
        sum(record.risk_matched for record in records),
        sum(record.risk_predicted for record in records),
        sum(record.risk_expected for record in records),
    )
    gaps = _detection_metrics(
        sum(record.gap_matched for record in records),
        sum(record.gap_predicted for record in records),
        sum(record.gap_expected for record in records),
    )
    overall = _detection_metrics(
        risk["true_positive"] + gaps["true_positive"],
        risk["predicted"] + gaps["predicted"],
        risk["expected"] + gaps["expected"],
    )
    severity_total = sum(record.severity_total for record in records)
    policy_total = sum(record.policy_total for record in records)
    evidence_total = sum(record.evidence_total for record in records)
    return {
        "risk_detection": risk,
        "compliance_gap_detection": gaps,
        "overall_detection": overall,
        "severity_accuracy_on_matched": _divide(
            sum(record.severity_correct for record in records), severity_total
        ),
        "policy_mapping_accuracy_on_matched": _divide(
            sum(record.policy_correct for record in records), policy_total
        ),
        "evidence_locator_accuracy_on_matched": _divide(
            sum(record.evidence_correct for record in records), evidence_total
        ),
        "schema_validity": 1.0 if records else 0.0,
    }


def serialize_record(record: GoldenRecord) -> dict[str, Any]:
    return {
        "case_id": record.case_id,
        "phase": record.phase,
        "skill_id": record.skill_id,
        "repeat": record.repeat,
        "risk": {
            "expected": record.risk_expected,
            "predicted": record.risk_predicted,
            "matched": record.risk_matched,
        },
        "compliance_gaps": {
            "expected": record.gap_expected,
            "predicted": record.gap_predicted,
            "matched": record.gap_matched,
        },
        "matches": list(record.matches),
    }


def _match_items(
    predicted: list[PredictedItem],
    expected: list[ExpectedItem],
    *,
    predicted_id: Callable[[PredictedItem], str],
    predicted_text: Callable[[PredictedItem], str],
    expected_id: Callable[[ExpectedItem], str],
    expected_terms: Callable[[ExpectedItem], list[str]],
) -> list[tuple[int, int, float]]:
    candidates: list[tuple[float, int, int]] = []
    for predicted_index, predicted_item in enumerate(predicted):
        for expected_index, expected_item in enumerate(expected):
            score = _match_score(
                predicted_id(predicted_item),
                predicted_text(predicted_item),
                expected_id(expected_item),
                expected_terms(expected_item),
            )
            if score >= 0.6:
                candidates.append((score, predicted_index, expected_index))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    used_predicted: set[int] = set()
    used_expected: set[int] = set()
    matches: list[tuple[int, int, float]] = []
    for score, predicted_index, expected_index in candidates:
        if predicted_index in used_predicted or expected_index in used_expected:
            continue
        used_predicted.add(predicted_index)
        used_expected.add(expected_index)
        matches.append((predicted_index, expected_index, round(score, 6)))
    return matches


def _match_score(
    predicted_id: str,
    predicted_text: str,
    expected_id: str,
    expected_terms: list[str],
) -> float:
    if expected_id and _normalize(predicted_id) == _normalize(expected_id):
        return 1.0
    text = _normalize(predicted_text)
    terms = [_normalize(term) for term in expected_terms if _normalize(term)]
    if not terms:
        return 0.0
    return sum(term in text for term in terms) / len(terms)


def _evidence_matches(
    source_ref: str | None,
    citation_ids: list[str],
    expected_locators: list[str],
    citations: dict[str, Any],
) -> bool:
    observed = {source_ref or "", *citation_ids}
    for citation_id in citation_ids:
        citation = citations.get(citation_id)
        if citation is None:
            continue
        observed.update(
            {
                citation.id,
                citation.locator or "",
                citation.paragraph_id or "",
            }
        )
    normalized_observed = {_normalize(value) for value in observed if value}
    return bool(
        normalized_observed
        & {_normalize(locator) for locator in expected_locators if locator}
    )


def _detection_metrics(matched: int, predicted: int, expected: int) -> dict[str, Any]:
    precision = _divide(matched, predicted)
    recall = _divide(matched, expected)
    return {
        "expected": expected,
        "predicted": predicted,
        "true_positive": matched,
        "false_positive": predicted - matched,
        "false_negative": expected - matched,
        "precision": precision,
        "recall": recall,
        "f1": _divide(2 * precision * recall, precision + recall),
    }


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
