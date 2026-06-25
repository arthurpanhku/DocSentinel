# ADR-002: Evidence-First Assessment Model

- Status: Accepted
- Date: 2026-06-25

## Context

The current report schema stores report-level sources, but a reviewer cannot
always prove which evidence supports each finding or control conclusion.

## Decision

The primary assessment unit is a `ControlAssessment`, not a whole report.

```text
FrameworkPack
  -> Control
  -> ControlAssessment
  -> Evidence[]
  -> ReviewDecision
```

Each evidence record contains:

- project and document identifiers
- immutable document version/hash
- page, paragraph, table, or chunk locator
- exact excerpt
- extraction method
- optional retrieval score

Control conclusions are:

- `satisfied`
- `partially_satisfied`
- `not_satisfied`
- `not_applicable`
- `insufficient_evidence`

`satisfied`, `partially_satisfied`, and `not_satisfied` require at least one
valid source evidence record. `not_applicable` requires a reviewer rationale.

## Consequences

- Reports become projections of approved control assessments.
- Citations can be opened from the review interface.
- Benchmark evaluation can score evidence precision independently from
  conclusion accuracy.
- Historical assessments may inform reasoning but cannot satisfy the current
  project's Evidence Gate.
