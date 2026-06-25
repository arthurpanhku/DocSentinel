# ADR-004: MCP and A2A Interoperability

## Status

Accepted for v5 Phase 1.

## Context

DocSentinel must integrate with coding agents, visual workflow builders, and
enterprise multi-agent runtimes without coupling the assessment core to each
vendor SDK. Agent-triggered work must preserve the same evidence, task,
activity, and human-review guarantees as console or REST submissions.

## Decision

DocSentinel exposes two complementary protocol surfaces:

- MCP exposes narrow tools and resources. Local stdio remains supported;
  Streamable HTTP is available at `/mcp/`.
- A2A 1.0 exposes DocSentinel as a remote specialist agent. Discovery uses
  `/.well-known/agent-card.json`; JSON-RPC messages are accepted at `/a2a`.

REST, MCP, and A2A all call the shared `AssessmentService`. Protocol adapters
must not call the LangGraph orchestrator or mutate task state directly.

Agent submissions always enable collaborative review. An external agent may
submit approved documents and read task state, but it may not approve, reject,
or bypass a human review gate.

Without `AGENT_GATEWAY_TOKEN`, protocol endpoints accept loopback clients only.
Network deployments require a bearer token, TLS, and preferably an upstream
OIDC-aware proxy. MCP DNS-rebinding protection remains enabled, so deployments
must explicitly allow trusted Host and Origin values. The public Agent Card and
non-secret status endpoint remain discoverable.

## Consequences

- Agent platforms integrate through standards instead of vendor-specific core
  dependencies.
- Security and task behavior stay consistent across entry points.
- The first A2A release accepts references to server-side approved paths. A
  future document-handle API should replace paths for cross-host workflows.
- OAuth 2.1, signed Agent Cards, task streaming, cancellation, and persistent
  task storage remain later hardening work.
