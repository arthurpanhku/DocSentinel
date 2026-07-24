"""Claim-level grounding metrics for threat evidence verification."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.assessment import Threat

VerificationStatus = Literal[
    "supported",
    "contradicted",
    "insufficient_evidence",
]


class GroundingScorecard(BaseModel):
    total: int = 0
    correct: int = 0
    status_accuracy: float = 0.0
    supported_precision: float = 0.0
    supported_recall: float = 0.0
    supported_f1: float = 0.0
    contradiction_recall: float = 0.0
    abstention_rate: float = 0.0
    citation_validity: float = 0.0
    confusion: dict[str, dict[str, int]] = Field(default_factory=dict)


def _divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _threat_value(threat: Threat | dict[str, Any], key: str) -> Any:
    if isinstance(threat, Threat):
        return getattr(threat, key)
    return threat.get(key)


def _predicted_status(threat: Threat | dict[str, Any]) -> str:
    verification = _threat_value(threat, "verification")
    if verification is None:
        return "insufficient_evidence"
    if hasattr(verification, "status"):
        return str(verification.status)
    if isinstance(verification, dict):
        return str(verification.get("status") or "insufficient_evidence")
    return "insufficient_evidence"


def _citation_ids(threat: Threat | dict[str, Any]) -> list[str]:
    values = _threat_value(threat, "citation_ids") or []
    return [str(value) for value in values]


def score_threat_grounding(
    predicted: list[Threat | dict[str, Any]],
    expected: list[dict[str, Any]],
    *,
    valid_source_ids: set[str] | None = None,
) -> GroundingScorecard:
    """Score verifier status and citation validity on ID-aligned threat cases."""
    predicted_by_id = {
        str(_threat_value(threat, "id")): threat
        for threat in predicted
        if _threat_value(threat, "id")
    }
    confusion: dict[str, dict[str, int]] = {}
    correct = 0
    supported_tp = 0
    supported_fp = 0
    supported_fn = 0
    contradicted_total = 0
    contradicted_correct = 0
    abstentions = 0
    citation_total = 0
    citation_valid = 0

    for item in expected:
        threat_id = str(item.get("id") or "")
        expected_status = str(
            item.get("verification_status") or "insufficient_evidence"
        )
        predicted_threat = predicted_by_id.get(threat_id)
        predicted_status = (
            _predicted_status(predicted_threat)
            if predicted_threat is not None
            else "insufficient_evidence"
        )
        confusion.setdefault(expected_status, {})
        confusion[expected_status][predicted_status] = (
            confusion[expected_status].get(predicted_status, 0) + 1
        )

        if predicted_status == expected_status:
            correct += 1
        if expected_status == "supported":
            if predicted_status == "supported":
                supported_tp += 1
            else:
                supported_fn += 1
        elif predicted_status == "supported":
            supported_fp += 1
        if expected_status == "contradicted":
            contradicted_total += 1
            if predicted_status == "contradicted":
                contradicted_correct += 1
        if predicted_status == "insufficient_evidence":
            abstentions += 1

        if predicted_threat is not None:
            ids = _citation_ids(predicted_threat)
            citation_total += len(ids)
            if valid_source_ids is None:
                citation_valid += len(ids)
            else:
                citation_valid += sum(
                    citation_id in valid_source_ids for citation_id in ids
                )

    total = len(expected)
    precision = _divide(supported_tp, supported_tp + supported_fp)
    recall = _divide(supported_tp, supported_tp + supported_fn)
    f1 = _divide(2 * precision * recall, precision + recall)
    return GroundingScorecard(
        total=total,
        correct=correct,
        status_accuracy=_divide(correct, total),
        supported_precision=precision,
        supported_recall=recall,
        supported_f1=f1,
        contradiction_recall=_divide(contradicted_correct, contradicted_total),
        abstention_rate=_divide(abstentions, total),
        citation_validity=_divide(citation_valid, citation_total),
        confusion=confusion,
    )
