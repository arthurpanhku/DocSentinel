from app.models.assessment import EvidenceVerification, Threat
from evals.scoring.scorers.grounding import score_threat_grounding


def _threat(
    threat_id: str,
    status: str,
    citation_ids: list[str] | None = None,
) -> Threat:
    return Threat(
        id=threat_id,
        category="Tampering",
        description=f"Threat {threat_id}",
        citation_ids=citation_ids or [],
        verification=EvidenceVerification(
            status=status,
            support_score=0.8,
            rationale="test verdict",
            evidence_ids=citation_ids or [],
        ),
    )


def test_grounding_scorer_reports_status_and_citation_quality():
    predicted = [
        _threat("T1", "supported", ["E1"]),
        _threat("T2", "insufficient_evidence"),
        _threat("T3", "supported", ["INVENTED"]),
    ]
    expected = [
        {"id": "T1", "verification_status": "supported"},
        {"id": "T2", "verification_status": "contradicted"},
        {"id": "T3", "verification_status": "insufficient_evidence"},
    ]

    score = score_threat_grounding(
        predicted,
        expected,
        valid_source_ids={"E1"},
    )

    assert score.total == 3
    assert score.correct == 1
    assert score.status_accuracy == 1 / 3
    assert score.supported_precision == 0.5
    assert score.supported_recall == 1.0
    assert score.contradiction_recall == 0.0
    assert score.abstention_rate == 1 / 3
    assert score.citation_validity == 0.5
