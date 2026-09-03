"""Offline-first verification of DSSE-wrapped SLSA provenance v1."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Protocol

from app.models.evidence import (
    EvidenceEnvelope,
    EvidenceProducer,
    EvidenceSignature,
    EvidenceSubject,
    EvidenceValidation,
)

IN_TOTO_STATEMENT_V1 = "https://in-toto.io/Statement/v1"
SLSA_PROVENANCE_V1 = "https://slsa.dev/provenance/v1"
DSSE_IN_TOTO_PAYLOAD_TYPE = "application/vnd.in-toto+json"


class SignatureVerifier(Protocol):
    def verify(
        self,
        *,
        payload_type: str,
        payload: bytes,
        signatures: list[dict[str, Any]],
    ) -> tuple[bool, str | None]: ...


class RejectUnsignedVerifier:
    """Safe default: cryptographic trust must be supplied by the operator."""

    def verify(
        self,
        *,
        payload_type: str,
        payload: bytes,
        signatures: list[dict[str, Any]],
    ) -> tuple[bool, str | None]:
        del payload_type, payload
        if not signatures:
            return False, "DSSE envelope has no signatures"
        return False, "No trusted signature verifier is configured"


@dataclass(frozen=True)
class SlsaExpectations:
    trusted_builders: dict[str, int] = field(default_factory=dict)
    allowed_build_types: frozenset[str] = frozenset()
    expected_source_uri: str | None = None
    require_signature: bool = True
    trust_policy_version: str = "1.0"


@dataclass(frozen=True)
class SlsaVerificationResult:
    verified: bool
    slsa_build_level: int
    errors: tuple[str, ...]
    evidence: EvidenceEnvelope


def _decode_envelope(envelope: dict[str, Any]) -> tuple[str, bytes, dict[str, Any]]:
    payload_type = str(envelope.get("payloadType") or "")
    if payload_type != DSSE_IN_TOTO_PAYLOAD_TYPE:
        raise ValueError(f"Unsupported DSSE payloadType: {payload_type or '<missing>'}")
    payload_text = envelope.get("payload")
    if not isinstance(payload_text, str):
        raise ValueError("DSSE payload must be base64 text")
    try:
        payload = base64.b64decode(payload_text, validate=True)
        statement = json.loads(payload)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("DSSE payload is not valid base64-encoded JSON") from exc
    if not isinstance(statement, dict):
        raise ValueError("in-toto statement must be a JSON object")
    return payload_type, payload, statement


def _source_uris(predicate: dict[str, Any]) -> set[str]:
    definition = predicate.get("buildDefinition") or {}
    dependencies = definition.get("resolvedDependencies") or []
    return {
        str(item.get("uri"))
        for item in dependencies
        if isinstance(item, dict) and item.get("uri")
    }


def verify_slsa_dsse(
    *,
    envelope: dict[str, Any],
    artifact: bytes,
    expectations: SlsaExpectations,
    signature_verifier: SignatureVerifier | None = None,
    source_uri: str | None = None,
) -> SlsaVerificationResult:
    checked_at = datetime.now(UTC)
    artifact_digest = sha256(artifact).hexdigest()
    errors: list[str] = []
    try:
        payload_type, payload, statement = _decode_envelope(envelope)
    except ValueError as exc:
        statement = {}
        payload_type = str(envelope.get("payloadType") or "")
        payload = b""
        errors.append(str(exc))

    if statement.get("_type") != IN_TOTO_STATEMENT_V1:
        errors.append("Statement _type is not in-toto Statement v1")
    if statement.get("predicateType") != SLSA_PROVENANCE_V1:
        errors.append("predicateType is not SLSA Provenance v1")

    subjects = statement.get("subject") or []
    subject_matches = any(
        isinstance(item, dict)
        and isinstance(item.get("digest"), dict)
        and str(item["digest"].get("sha256", "")).lower() == artifact_digest
        for item in subjects
    )
    if not subject_matches:
        errors.append("Provenance subject digest does not match the artifact")

    predicate = statement.get("predicate") or {}
    run_details = predicate.get("runDetails") or {}
    builder_id = str((run_details.get("builder") or {}).get("id") or "")
    if builder_id not in expectations.trusted_builders:
        errors.append("Builder identity is not trusted")

    definition = predicate.get("buildDefinition") or {}
    build_type = str(definition.get("buildType") or "")
    if (
        expectations.allowed_build_types
        and build_type not in expectations.allowed_build_types
    ):
        errors.append("Build type is not allowed")
    if (
        expectations.expected_source_uri
        and expectations.expected_source_uri not in _source_uris(predicate)
    ):
        errors.append(
            "Expected source repository was not present in resolved dependencies"
        )

    signatures = envelope.get("signatures") or []
    verifier = signature_verifier or RejectUnsignedVerifier()
    signature_ok, signature_identity = verifier.verify(
        payload_type=payload_type,
        payload=payload,
        signatures=signatures if isinstance(signatures, list) else [],
    )
    if expectations.require_signature and not signature_ok:
        errors.append("Provenance signature could not be verified")

    verified = not errors
    level = expectations.trusted_builders.get(builder_id, 0) if verified else 0
    evidence = EvidenceEnvelope(
        kind="slsa-provenance",
        media_type="application/vnd.dsse.envelope.v1+json",
        schema_uri=SLSA_PROVENANCE_V1,
        source_uri=source_uri,
        digests={
            "sha256": sha256(json.dumps(envelope, sort_keys=True).encode()).hexdigest()
        },
        producer=EvidenceProducer(
            name="slsa-verifier",
            version="1.0",
            identity=builder_id or None,
        ),
        subject=EvidenceSubject(
            repository=expectations.expected_source_uri,
            commit_sha=None,
        ),
        collected_at=checked_at,
        signature=EvidenceSignature(
            scheme="dsse",
            certificate_identity=signature_identity,
            verified=signature_ok,
        ),
        validation=EvidenceValidation(
            validator="docsentinel.slsa",
            version="1.0",
            status="valid" if verified else "invalid",
            checked_at=checked_at,
            errors=tuple(errors),
        ),
        metadata={
            "artifact_sha256": artifact_digest,
            "builder_id": builder_id,
            "build_type": build_type,
            "slsa_build_level": level,
            "trust_policy_version": expectations.trust_policy_version,
        },
    )
    return SlsaVerificationResult(
        verified=verified,
        slsa_build_level=level,
        errors=tuple(errors),
        evidence=evidence,
    )
