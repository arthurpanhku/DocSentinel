import base64
import json
from hashlib import sha256

from app.services.slsa_verifier import SlsaExpectations, verify_slsa_dsse


class TrustedFixtureVerifier:
    def verify(self, *, payload_type, payload, signatures):
        assert payload_type == "application/vnd.in-toto+json"
        return (bool(payload and signatures), "builder@example.com")


def _envelope(artifact: bytes, *, digest: str | None = None, builder="builder.example"):
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": "artifact.tar.gz",
                "digest": {"sha256": digest or sha256(artifact).hexdigest()},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://example.com/build/v1",
                "externalParameters": {},
                "resolvedDependencies": [{"uri": "git+https://example.com/repo"}],
            },
            "runDetails": {"builder": {"id": builder}},
        },
    }
    return {
        "payloadType": "application/vnd.in-toto+json",
        "payload": base64.b64encode(json.dumps(statement).encode()).decode(),
        "signatures": [{"keyid": "fixture", "sig": "fixture"}],
    }


def test_verified_provenance_derives_configured_builder_level():
    artifact = b"release artifact"
    result = verify_slsa_dsse(
        envelope=_envelope(artifact),
        artifact=artifact,
        expectations=SlsaExpectations(
            trusted_builders={"builder.example": 2},
            allowed_build_types=frozenset({"https://example.com/build/v1"}),
            expected_source_uri="git+https://example.com/repo",
        ),
        signature_verifier=TrustedFixtureVerifier(),
    )
    assert result.verified is True
    assert result.slsa_build_level == 2
    assert result.evidence.validation.status == "valid"
    assert result.evidence.signature.verified is True


def test_tampered_artifact_and_untrusted_builder_fail_closed():
    artifact = b"release artifact"
    result = verify_slsa_dsse(
        envelope=_envelope(
            artifact,
            digest=sha256(b"different").hexdigest(),
            builder="untrusted.example",
        ),
        artifact=artifact,
        expectations=SlsaExpectations(trusted_builders={"builder.example": 2}),
        signature_verifier=TrustedFixtureVerifier(),
    )
    assert result.verified is False
    assert result.slsa_build_level == 0
    assert any("digest" in error for error in result.errors)
    assert any("Builder" in error for error in result.errors)
