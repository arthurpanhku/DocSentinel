from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.models.evidence import (
    EvidenceEnvelope,
    EvidenceProducer,
    EvidenceSignature,
    EvidenceValidation,
    GateFinding,
    GatePolicy,
    RiskWaiver,
)
from app.services.evidence_gate import evaluate_gate


def _evidence(kind: str, *, valid: bool = True, signed: bool = False):
    now = datetime.now(UTC)
    return EvidenceEnvelope(
        kind=kind,
        media_type="application/json",
        digests={"sha256": sha256(kind.encode()).hexdigest()},
        producer=EvidenceProducer(name="fixture", version="1"),
        collected_at=now,
        signature=(
            EvidenceSignature(scheme="test", verified=signed) if signed else None
        ),
        validation=EvidenceValidation(
            validator="fixture",
            version="1",
            status="valid" if valid else "invalid",
            checked_at=now,
        ),
    )


def test_gate_is_deterministic_and_requires_human_review():
    now = datetime(2026, 9, 3, tzinfo=UTC)
    evidence = [_evidence("sarif"), _evidence("slsa-provenance", signed=True)]
    policy = GatePolicy(
        version="v1",
        required_evidence_kinds=("sarif", "slsa-provenance"),
        require_verified_signatures_for=("slsa-provenance",),
    )

    first = evaluate_gate(policy=policy, evidence=evidence, evaluated_at=now)
    second = evaluate_gate(policy=policy, evidence=reversed(evidence), evaluated_at=now)

    assert first.outcome == "conditional"
    assert first.input_digest == second.input_digest
    assert first.human_approval_required is True


def test_expired_waiver_cannot_bypass_blocking_finding():
    now = datetime(2026, 9, 3, tzinfo=UTC)
    finding = GateFinding(
        finding_id="F-1",
        control_id="GEN-SC-01",
        severity="critical",
    )
    waiver = RiskWaiver(
        waiver_id="W-1",
        finding_ids=("F-1",),
        owner="service-owner",
        rationale="Temporary mitigation",
        compensating_controls=("network isolation",),
        approved_by="security-approver",
        approved_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=1),
    )

    decision = evaluate_gate(
        policy=GatePolicy(version="v1", require_human_approval=False),
        evidence=[_evidence("document")],
        findings=[finding],
        waivers=[waiver],
        evaluated_at=now,
    )

    assert decision.outcome == "fail"
    assert not decision.applied_waiver_ids


def test_non_waivable_control_remains_blocking():
    now = datetime(2026, 9, 3, tzinfo=UTC)
    finding = GateFinding(
        finding_id="F-1",
        control_id="RELEASE-SIGNATURE",
        severity="high",
    )
    waiver = RiskWaiver(
        waiver_id="W-1",
        control_ids=("RELEASE-SIGNATURE",),
        owner="owner",
        rationale="Requested bypass",
        compensating_controls=("manual checksum",),
        approved_by="approver",
        approved_at=now,
        expires_at=now + timedelta(days=1),
    )
    decision = evaluate_gate(
        policy=GatePolicy(
            version="v1",
            non_waivable_controls=("RELEASE-SIGNATURE",),
            require_human_approval=False,
        ),
        evidence=[_evidence("document")],
        findings=[finding],
        waivers=[waiver],
        evaluated_at=now,
    )
    assert decision.outcome == "fail"


def test_unvalidated_evidence_fails_closed():
    item = _evidence("sarif")
    item = item.model_copy(
        update={
            "validation": item.validation.model_copy(update={"status": "not_verified"})
        }
    )
    decision = evaluate_gate(
        policy=GatePolicy(version="v1", require_human_approval=False),
        evidence=[item],
    )
    assert decision.outcome == "fail"
