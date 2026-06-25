# RFC-001: Product Trust Contract

- Status: Accepted
- Date: 2026-06-25
- Target: DocSentinel v5

## Product Position

DocSentinel is a local-first decision-support system for security consultants
and information security managers. It accelerates review of project material
against versioned security frameworks. It does not replace the accountable
human reviewer.

## Trust Boundaries

1. Customer documents remain inside the customer-controlled environment.
2. An external LLM provider may receive document content only when explicitly
   configured by the operator.
3. LLM output is always a draft until a human reviewer records a decision.
4. The LLM cannot decide filesystem access, applicable frameworks, user
   permissions, or whether a report is final.
5. Customer feedback is not shared across deployments by default.

## Required Gates

### Evidence Gate

- Every positive or negative control conclusion must reference source evidence.
- Evidence must identify a document version and a stable page, paragraph,
  table, or chunk locator.
- Missing or invalid evidence forces `insufficient_evidence`.
- Generated text and historical reports must never be represented as source
  evidence from the current project.

### Human Gate

- All generated assessments begin in `draft`.
- Only an authorized reviewer can approve, reject, or edit a conclusion.
- Review decisions record actor, timestamp, previous value, new value, and
  rationale.
- Only approved conclusions may appear in a final report.

### Release Gate

- Model, prompt, retrieval, parser, and framework-pack changes run against the
  benchmark suite.
- A release is blocked when critical-finding recall, citation validity, or
  consistency falls below the approved threshold.

## Product Success Measures

- Critical finding recall
- Control coverage recall
- Citation locator validity and precision
- Repeat-run consistency
- Expert acceptance and correction rate
- Review time saved against the manual baseline

## Explicit Non-Goals for v5

- Autonomous audit sign-off
- Cross-customer reinforcement learning
- Hosted SaaS operation
- Automatic framework selection based only on LLM reasoning
- Microservice decomposition before module boundaries are stable
