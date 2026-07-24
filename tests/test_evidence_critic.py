import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.assessment import AssessmentReport, Threat, ThreatModel
from app.models.parser import ParsedDocument, ParsedDocumentMetadata
from app.services.evidence_critic import (
    build_document_passages,
    verify_threat_model_evidence,
)


def _document() -> ParsedDocument:
    return ParsedDocument(
        content=(
            "# Checkout architecture\n"
            "The public API gateway validates OIDC access tokens before forwarding "
            "requests to the payment service.\n\n"
            "# Webhooks\n"
            "The public payment webhook accepts event payloads. HMAC signature "
            "validation is planned but is not implemented.\n"
        ),
        metadata=ParsedDocumentMetadata(
            filename="checkout.md",
            type="md",
            file_hash="abc123def456",
        ),
    )


def _report(phase: str = "design") -> AssessmentReport:
    return AssessmentReport(
        task_id="00000000-0000-0000-0000-000000000001",
        phase=phase,
        status="completed",
        summary="Design review",
        threat_model=ThreatModel(
            methodology="STRIDE",
            threats=[
                Threat(
                    id="T1",
                    category="Spoofing",
                    description=(
                        "Attackers may bypass authentication at the API gateway."
                    ),
                    affected_component="API gateway",
                ),
                Threat(
                    id="T2",
                    category="Tampering",
                    description="Unsigned webhook payloads may be modified in transit.",
                    affected_component="payment webhook",
                ),
            ],
        ),
    )


def test_build_document_passages_creates_stable_current_document_locators():
    first = build_document_passages([_document()])
    second = build_document_passages([_document()])

    assert [passage.id for passage in first] == [passage.id for passage in second]
    assert first[0].id.startswith("DOC-1-L1-L2-abc123def4")
    assert first[0].locator == "L1-L2"
    assert first[0].document_hash == "abc123def456"


@pytest.mark.asyncio
async def test_evidence_critic_verifies_threats_and_attaches_exact_sources():
    passages = build_document_passages([_document()])
    gateway_evidence = passages[0].id
    webhook_evidence = passages[1].id
    response = {
        "verdicts": [
            {
                "threat_id": "T1",
                "status": "contradicted",
                "support_score": 0.91,
                "evidence_ids": [],
                "counterevidence_ids": [gateway_evidence],
                "rationale": "The gateway explicitly validates OIDC tokens.",
            },
            {
                "threat_id": "T2",
                "status": "supported",
                "support_score": 0.96,
                "evidence_ids": [webhook_evidence],
                "counterevidence_ids": [],
                "rationale": "The public webhook has no implemented HMAC validation.",
            },
        ]
    }

    with patch(
        "app.services.evidence_critic.invoke_llm",
        new=AsyncMock(return_value=f"```json\n{json.dumps(response)}\n```"),
    ) as verifier:
        result = await verify_threat_model_evidence(_report(), [_document()])

    verifier.assert_awaited_once()
    assert result.threat_model is not None
    assert result.threat_model.threats[0].verification is not None
    assert result.threat_model.threats[0].verification.status == "contradicted"
    assert result.threat_model.threats[1].verification is not None
    assert result.threat_model.threats[1].verification.status == "supported"
    assert result.threat_model.verification_summary is not None
    assert result.threat_model.verification_summary.supported == 1
    assert result.threat_model.verification_summary.contradicted == 1
    assert {source.id for source in result.sources} == {
        gateway_evidence,
        webhook_evidence,
    }
    assert all(source.source_kind == "current_document" for source in result.sources)
    assert all(
        source.evidence_link.startswith("document://") for source in result.sources
    )


@pytest.mark.asyncio
async def test_evidence_critic_rejects_invented_citation_ids():
    response = {
        "verdicts": [
            {
                "threat_id": "T1",
                "status": "supported",
                "support_score": 0.99,
                "evidence_ids": ["DOC-INVENTED"],
                "counterevidence_ids": [],
                "rationale": "Invented citation.",
            }
        ]
    }
    with patch(
        "app.services.evidence_critic.invoke_llm",
        new=AsyncMock(return_value=json.dumps(response)),
    ):
        result = await verify_threat_model_evidence(_report(), [_document()])

    assert result.threat_model is not None
    verdict = result.threat_model.threats[0].verification
    assert verdict is not None
    assert verdict.status == "insufficient_evidence"
    assert verdict.evidence_ids == []
    assert "valid current-document citation" in verdict.rationale
    assert result.sources == []


@pytest.mark.asyncio
async def test_evidence_critic_handles_malformed_reference_arrays_safely():
    response = {
        "verdicts": [
            {
                "threat_id": "T1",
                "status": "supported",
                "support_score": 0.99,
                "evidence_ids": "DOC-1-L1-L2",
                "counterevidence_ids": None,
                "rationale": "Malformed references.",
            }
        ]
    }
    with patch(
        "app.services.evidence_critic.invoke_llm",
        new=AsyncMock(return_value=json.dumps(response)),
    ):
        result = await verify_threat_model_evidence(_report(), [_document()])

    assert result.threat_model is not None
    verdict = result.threat_model.threats[0].verification
    assert verdict is not None
    assert verdict.status == "insufficient_evidence"


@pytest.mark.asyncio
async def test_evidence_critic_fails_safe_when_inference_is_unavailable():
    with patch(
        "app.services.evidence_critic.invoke_llm",
        new=AsyncMock(side_effect=RuntimeError("offline")),
    ):
        result = await verify_threat_model_evidence(_report(), [_document()])

    assert result.threat_model is not None
    assert result.threat_model.verification_summary is not None
    assert result.threat_model.verification_summary.status == "fallback"
    assert result.threat_model.verification_summary.insufficient_evidence == 2
    assert {
        threat.verification.status
        for threat in result.threat_model.threats
        if threat.verification is not None
    } == {"insufficient_evidence"}


@pytest.mark.asyncio
async def test_evidence_critic_only_runs_for_design_phase():
    verifier = AsyncMock()
    with patch("app.services.evidence_critic.invoke_llm", new=verifier):
        result = await verify_threat_model_evidence(
            _report(phase="testing"),
            [_document()],
        )

    verifier.assert_not_awaited()
    assert result.threat_model is not None
    assert result.threat_model.verification_summary is None
