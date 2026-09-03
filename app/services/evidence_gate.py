"""Deterministic SSDLC evidence validation and release-gate evaluation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from hashlib import sha256

from app.models.evidence import (
    EvidenceEnvelope,
    GateDecision,
    GateFinding,
    GatePolicy,
    RiskWaiver,
)

SUPPORTED_EVIDENCE_KINDS = {
    "document",
    "sarif",
    "sbom-cyclonedx",
    "sbom-spdx",
    "slsa-provenance",
    "vex",
    "test-report",
}


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _active_waiver(
    finding: GateFinding,
    waivers: Iterable[RiskWaiver],
    now: datetime,
) -> RiskWaiver | None:
    for waiver in waivers:
        expires_at = waiver.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            continue
        if (
            finding.finding_id in waiver.finding_ids
            or finding.control_id in waiver.control_ids
        ):
            return waiver
    return None


def evaluate_gate(
    *,
    policy: GatePolicy,
    evidence: Iterable[EvidenceEnvelope],
    findings: Iterable[GateFinding] = (),
    waivers: Iterable[RiskWaiver] = (),
    evaluated_at: datetime | None = None,
) -> GateDecision:
    """Evaluate identical inputs to an identical outcome and input digest."""

    now = evaluated_at or datetime.now(UTC)
    evidence_items = tuple(sorted(evidence, key=lambda item: str(item.evidence_id)))
    finding_items = tuple(sorted(findings, key=lambda item: item.finding_id))
    waiver_items = tuple(sorted(waivers, key=lambda item: item.waiver_id))
    reasons: list[str] = []
    applied: list[str] = []

    kinds = {item.kind for item in evidence_items}
    missing = sorted(set(policy.required_evidence_kinds) - kinds)
    if missing:
        reasons.append(f"Missing required evidence kinds: {', '.join(missing)}")

    invalid = [
        item
        for item in evidence_items
        if item.kind not in SUPPORTED_EVIDENCE_KINDS
        or item.validation.status != "valid"
    ]
    if invalid:
        reasons.append(
            "Invalid or unsupported evidence: "
            + ", ".join(str(item.evidence_id) for item in invalid)
        )

    unverified_signatures = [
        item
        for item in evidence_items
        if item.kind in policy.require_verified_signatures_for
        and (item.signature is None or not item.signature.verified)
    ]
    if unverified_signatures:
        reasons.append(
            "Required signature was not verified: "
            + ", ".join(str(item.evidence_id) for item in unverified_signatures)
        )

    blocking: list[GateFinding] = []
    for finding in finding_items:
        if (
            finding.status != "open"
            or finding.severity not in policy.blocking_severities
        ):
            continue
        waiver = _active_waiver(finding, waiver_items, now)
        if waiver and finding.control_id not in policy.non_waivable_controls:
            applied.append(waiver.waiver_id)
            continue
        blocking.append(finding)
    if blocking:
        reasons.append(
            "Open blocking findings: "
            + ", ".join(finding.finding_id for finding in blocking)
        )

    if invalid or unverified_signatures or blocking:
        outcome = "fail"
    elif missing:
        outcome = "insufficient_evidence"
    elif applied or policy.require_human_approval:
        outcome = "conditional"
    else:
        outcome = "pass"

    if not reasons:
        reasons.append("All deterministic evidence and finding checks passed.")
    if policy.require_human_approval:
        reasons.append("Authorized human approval is required before release.")

    inputs = {
        "evaluated_at": now.isoformat(),
        "policy": policy.model_dump(mode="json"),
        "evidence": [item.model_dump(mode="json") for item in evidence_items],
        "findings": [item.model_dump(mode="json") for item in finding_items],
        "waivers": [item.model_dump(mode="json") for item in waiver_items],
    }
    return GateDecision(
        outcome=outcome,
        policy_version=policy.version,
        evaluated_at=now,
        evidence_ids=tuple(item.evidence_id for item in evidence_items),
        finding_ids=tuple(item.finding_id for item in finding_items),
        applied_waiver_ids=tuple(sorted(set(applied))),
        reasons=tuple(reasons),
        human_approval_required=policy.require_human_approval,
        input_digest=_canonical_digest(inputs),
    )
