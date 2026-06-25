from app.models.assessment import AssessmentReport, Remediation, RiskItem


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
