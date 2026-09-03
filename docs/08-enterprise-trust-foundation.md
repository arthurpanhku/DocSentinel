# Enterprise SSDLC Trust Foundation

This document describes the maintainer-owned trust boundary introduced for the
next DocSentinel architecture increment. The goal is to make an assessment or
release decision reproducible, attributable, and safe to consume from another
company's SSDLC rather than merely plausible to a human reader.

## Security model

Every non-authentication governance route requires an authenticated principal.
Users and projects carry a `tenant_id`; project lookups return `404` when the
principal belongs to another tenant so resource existence is not disclosed.
Assessment lifecycle records use the same tenant boundary.
The shared MCP/A2A gateway credential is scoped to the configured
`AGENT_GATEWAY_TENANT_ID`; deployments needing per-client identities should use
separate gateway instances until credential-to-tenant mapping is implemented.

Reviewer and transition actor IDs are derived from the access token. Actor IDs
supplied by older clients are accepted only for compatibility and ignored.
Gate approval follows the explicit transition table in
`app/models/governance/submission.py`, and the principal must hold a role allowed
for that transition. A gate submitter cannot approve or reject the same gate.

Security-sensitive mutations append a `GovernanceAuditLog` row in the same
database transaction. Each row includes the previous event digest for its tenant
and its own SHA-256 digest. This makes deletion or modification detectable during
audit export. The chain is tamper-evident, not an external timestamping service;
operators needing non-repudiation should stream it to immutable storage.

## Durable assessment lifecycle

Assessment tasks are stored in `assessment_tasks` as indexed lifecycle metadata
plus a versioned JSON payload. The payload preserves the task contract, execution
inputs needed for recovery, review history, plan, evaluation, and remediation
tracking. Submission supports a tenant-scoped idempotency key.

At application startup, resumable `pending`, `running`, or `interrupted` tasks are
scheduled again. Tasks created with a custom in-process runner are marked
`interrupted` after restart because their executable cannot be reconstructed.
Execution is bounded by `ASSESSMENT_TASK_TIMEOUT_SECONDS`; transient timeout and
connection failures observe the task contract's retry limit. Operators may set
`ASSESSMENT_PERSISTENCE_ENABLED=false` only for ephemeral local development.

## Evidence Envelope and policy gate

`EvidenceEnvelope` is a provider-neutral, immutable contract with:

- subject and producer identity;
- a mandatory SHA-256 digest;
- collection and production timestamps;
- signature and validation results;
- source locators, confidentiality, retention, and derivation metadata.

The JSON Schema is published at `docs/schemas/evidence-envelope.json`.
`evaluate_gate` sorts and hashes all inputs before applying policy. It fails
closed for unsupported or unvalidated evidence, missing required signatures, and
open blocking findings. Waivers require an owner, approver, rationale,
compensating controls, and expiry; expired waivers and non-waivable controls
cannot bypass the gate. Human approval remains an explicit conditional outcome.

## SLSA provenance verification

The offline verifier accepts a DSSE envelope containing an in-toto Statement v1
with a SLSA Provenance v1 predicate. It checks:

1. envelope and predicate types;
2. the subject SHA-256 against the actual artifact bytes;
3. builder identity against the configured trust policy;
4. allowed build type and expected source repository;
5. the result of an operator-supplied signature verifier.

The default signature verifier always rejects. A deployment must integrate a
cryptographic verifier (for example, a Sigstore policy verifier) and must not
derive trust from an unverified identity string. A SLSA build level is emitted
only after every configured check succeeds, and comes from the trusted-builder
policy rather than untrusted provenance content.

Threats handled include artifact substitution, provenance substitution,
untrusted builders, unexpected build workflows, source confusion, unsigned
claims, stale waivers, and caller-forged reviewer identity. Key compromise,
malicious trusted builders, and compromise of the database plus application key
remain operator risks and require key rotation, isolated builders, immutable log
export, and incident response outside this component.

## Migration and rollback

Apply migrations before enabling the new application version:

```bash
alembic upgrade head
```

Migration `2f6c5f07a101` creates durable assessment tasks. Migration
`8d4e7c91b203` adds tenant identifiers, gate submitter identity, and the audit
hash chain. Existing records are assigned to the `default` tenant; operators
must map them to real tenants before exposing the service to multiple customers.
Legacy audit rows are deterministically chained during migration.

For rollback, first stop workers so no new task or audit rows are written, export
the affected tables, deploy the previous application, then run one revision at a
time:

```bash
alembic downgrade 2f6c5f07a101
alembic downgrade ebcc5bce6929
```

The second downgrade removes `assessment_tasks` and therefore deletes persisted
task history. Restore that table from the export if forward recovery is needed.
Disabling persistence is a runtime containment option, not a substitute for a
database rollback.

## Repository and release controls

CODEOWNERS marks trust-boundary code and workflows for maintainer review. The PR
Plan Gate requires an issue, implementation plan, verification, security impact,
and rollback section for high-risk paths. CodeQL and dependency update workflows
provide continuous scanning. Tagged releases build from the dependency lock,
emit checksums and an SPDX SBOM, and use GitHub artifact attestations for SLSA
provenance and the SBOM.

Repository administrators must still enable branch/ruleset enforcement for the
required CI, PR Plan Gate, CodeQL, and CODEOWNERS approvals after these workflows
land. Repository settings are intentionally not represented as source code.
