"""Versioned contracts for verifiable SSDLC evidence and gate decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _ImmutableContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class EvidenceSubject(_ImmutableContract):
    project_id: str | None = None
    repository: str | None = None
    commit_sha: str | None = None
    build_id: str | None = None
    release: str | None = None


class EvidenceProducer(_ImmutableContract):
    name: str
    version: str | None = None
    identity: str | None = None


class EvidenceSignature(_ImmutableContract):
    scheme: str
    key_id: str | None = None
    certificate_identity: str | None = None
    verified: bool = False
    transparency_log_entry: str | None = None


class EvidenceValidation(_ImmutableContract):
    validator: str
    version: str
    status: Literal["valid", "invalid", "unsupported", "not_verified"]
    checked_at: datetime
    errors: tuple[str, ...] = ()


class EvidenceLocator(_ImmutableContract):
    uri: str
    pointer: str | None = None
    description: str | None = None


class EvidenceEnvelope(_ImmutableContract):
    """Provider-neutral envelope. Validation status is never inferred by an LLM."""

    version: Literal["1.0"] = "1.0"
    evidence_id: UUID = Field(default_factory=uuid4)
    kind: str = Field(min_length=1, max_length=128)
    media_type: str = Field(min_length=1, max_length=255)
    schema_uri: str | None = None
    source_uri: str | None = None
    digests: dict[str, str] = Field(min_length=1)
    producer: EvidenceProducer
    subject: EvidenceSubject = Field(default_factory=EvidenceSubject)
    produced_at: datetime | None = None
    collected_at: datetime
    signature: EvidenceSignature | None = None
    validation: EvidenceValidation
    locators: tuple[EvidenceLocator, ...] = ()
    confidentiality: Literal["public", "internal", "confidential", "restricted"] = (
        "internal"
    )
    retention_policy: str | None = None
    derived_from: tuple[UUID, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("digests")
    @classmethod
    def validate_digests(cls, value: dict[str, str]) -> dict[str, str]:
        normalized = {
            algorithm.lower(): digest.lower() for algorithm, digest in value.items()
        }
        sha256 = normalized.get("sha256")
        if sha256 is None:
            raise ValueError("Evidence must include a sha256 digest")
        if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
            raise ValueError("sha256 digest must contain 64 hexadecimal characters")
        return normalized


class GateFinding(_ImmutableContract):
    finding_id: str
    control_id: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    status: Literal["open", "resolved", "accepted"] = "open"
    evidence_ids: tuple[UUID, ...] = ()


class RiskWaiver(_ImmutableContract):
    waiver_id: str
    finding_ids: tuple[str, ...] = ()
    control_ids: tuple[str, ...] = ()
    owner: str
    rationale: str = Field(min_length=1)
    compensating_controls: tuple[str, ...] = Field(min_length=1)
    approved_by: str
    approved_at: datetime
    expires_at: datetime


class GatePolicy(_ImmutableContract):
    version: str
    required_evidence_kinds: tuple[str, ...] = ()
    blocking_severities: tuple[Literal["critical", "high", "medium", "low"], ...] = (
        "critical",
        "high",
    )
    non_waivable_controls: tuple[str, ...] = ()
    require_verified_signatures_for: tuple[str, ...] = ()
    require_human_approval: bool = True


class GateDecision(_ImmutableContract):
    version: Literal["1.0"] = "1.0"
    decision_id: UUID = Field(default_factory=uuid4)
    outcome: Literal["pass", "fail", "conditional", "insufficient_evidence"]
    policy_version: str
    evaluated_at: datetime
    evidence_ids: tuple[UUID, ...]
    finding_ids: tuple[str, ...]
    applied_waiver_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...]
    human_approval_required: bool
    input_digest: str
