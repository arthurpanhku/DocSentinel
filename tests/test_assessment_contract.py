from app.models.assessment import (
    AssessmentReport,
    EvidenceVerification,
    Remediation,
    RiskItem,
    SourceCitation,
    Threat,
)


def test_report_contract_defaults_to_v2():
    report = AssessmentReport(
        task_id="00000000-0000-0000-0000-000000000000",
        status="completed",
        summary="Draft",
    )

    assert report.version == "2.0"
    assert report.vulnerabilities == []
    assert report.cross_phase_refs == []


def test_contract_accepts_critical_remediation_and_finding_evidence():
    remediation = Remediation(
        id="R1",
        action="Block release",
        priority="critical",
        related_gap_ids=["G1"],
    )
    risk = RiskItem(
        id="F1",
        title="Missing privileged access control",
        severity="critical",
        confidence=0.91,
        citation_ids=["E1"],
        phase="design",
    )

    assert remediation.priority == "critical"
    assert risk.citation_ids == ["E1"]


def test_contract_carries_threat_evidence_verdicts_and_stable_locators():
    verdict = EvidenceVerification(
        status="supported",
        support_score=0.93,
        rationale="The design exposes a public unsigned webhook.",
        evidence_ids=["DOC-1-L10-L12-abc"],
    )
    threat = Threat(
        id="T1",
        category="Tampering",
        description="Webhook payloads can be modified.",
        confidence=0.93,
        citation_ids=["DOC-1-L10-L12-abc"],
        verification=verdict,
    )
    source = SourceCitation(
        id="DOC-1-L10-L12-abc",
        file="architecture.md",
        excerpt="HMAC validation is not implemented.",
        document_hash="abcdef",
        locator="L10-L12",
        source_kind="current_document",
    )

    assert threat.verification is not None
    assert threat.verification.status == "supported"
    assert source.locator == "L10-L12"
    assert source.source_kind == "current_document"
