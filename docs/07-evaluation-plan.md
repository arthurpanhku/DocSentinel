# 07 — Evaluation Plan (`evals/`)

|                 |                                                                        |
| :-------------- | :--------------------------------------------------------------------- |
| **Status**      | [x] Draft \| [ ] In Review \| [ ] Approved                             |
| **Audience**    | DocSentinel maintainers + peers building AI-SSDLC evaluation harnesses |
| **Owner**       | TBD                                                                    |
| **Executor**    | Codex (implementation) — this doc is the executable spec               |

> **Why this exists.** Enterprise security teams do not adopt AI output on faith.
> The single most valuable asset DocSentinel can ship is *reproducible evidence
> of assessment quality* — per skill, per SSDLC phase, with a public methodology
> peers can reuse and contest. This document specifies that harness. It is written
> to be handed to Codex and executed milestone by milestone; it is also meant to
> read as a methodology reference for others building evals over
> document-review / agentic-security tools.

**Implementation note:** M0 and M1 are implemented. A focused Design-phase
Threat Evidence Critic scorer is also available for verdict accuracy,
supported precision/recall/F1, contradiction recall, abstention, citation
validity, and confusion reporting. This vertical slice supports the public demo
but does not mark the broader M2 or M5 milestones complete.

---

## 1. Goals and Non-Goals

### 1.1 Goals

1. Measure the **quality** of DocSentinel assessment reports against ground truth,
   broken down by **skill** and **SSDLC phase**.
2. Be **reproducible**: pinned datasets, pinned model configs, deterministic
   scoring, versioned scorecards. Anyone can re-run and get the same numbers.
3. Be **honest about uncertainty**: report variance across repeats, judge–human
   agreement, and known contamination risk — not just a single headline score.
4. Double as a **regression gate**: the same harness runs a fast subset in CI so
   a prompt/graph change that degrades quality is caught before merge.
5. Be **portable methodology**: the matching + scoring approach is documented so
   peers reviewing *any* AI-SSDLC tool can adopt it.

### 1.2 Non-Goals

- Not a general LLM leaderboard (MMLU-style). We score *this pipeline's* output.
- Not UI/UX testing, not load testing (see `docs/05-deployment-runbook.md`).
- Not a security review of DocSentinel itself (that is `SECURITY.md` / red-team).
- Not model training or fine-tuning. Eval only.

---

## 2. What We Measure

DocSentinel reports are **sets of structured items**, not single labels. The
report schema (`docs/schemas/assessment-report.json`) exposes these ground-truth-able
surfaces:

| Report field       | Artifact under test        | Ground-truth source (see §3)          | Primary metric family        |
| :----------------- | :------------------------- | :------------------------------------ | :--------------------------- |
| `threat_model.threats` | STRIDE/DREAD threat modeling | TM-Bench, ThreatModeling-LLM      | set precision / recall / F1  |
| `vulnerabilities`  | SAST/DAST triage           | OWASP Benchmark, D2A, SastBench       | binary TP/FP + FP-rate       |
| `risk_items`       | doc risk identification    | self-built golden set (§3.3)          | set precision / recall / F1  |
| `compliance_gaps`  | compliance gap analysis    | self-built golden set (§3.3)          | set precision / recall / F1  |
| (requirements tag) | security-requirement class | SecReq, PROMISE-NFR                   | classification P/R/F1        |
| `sources`          | citation grounding         | derived (span in source doc)          | attribution / hallucination  |
| `confidence`       | calibration                | correctness labels from above         | ECE / reliability curve      |

### 2.1 Metric definitions

- **Set detection (risks, threats, gaps):** after matching predicted items to
  ground-truth items (§5), report **precision, recall, F1** at the item level.
  Break down by severity band (critical/high vs medium/low) — missing a critical
  risk is not the same failure as missing a low one. Report a **severity-weighted
  recall** as the headline for security-team relevance.
- **Binary triage (SAST/DAST):** accuracy, precision, recall, F1, and — called out
  separately because analysts feel it most — **false-positive rate**. An over-flagging
  triage agent is worse than useless.
- **Classification (requirements):** standard P/R/F1 + confusion matrix.
- **Citation grounding:** fraction of predicted items whose `citation_ids` resolve
  to a source span that actually supports the claim (**attribution precision**);
  and **hallucination rate** = predicted items with no valid supporting citation.
- **Calibration:** bucket predictions by `confidence`, plot observed correctness
  per bucket, report **Expected Calibration Error**.
- **Cost/latency:** tokens, wall-clock, and $ per case (from provider metadata).
- **Stability:** every case run **N≥3** times at temperature 0; report **mean ± std**
  of F1 and a **consistency@N** (fraction of items that appear in all N runs).

> A scorecard that reports only mean F1 and hides variance is not credible to a
> security audience. Variance and judge-agreement are first-class outputs.

---

## 3. Datasets

Split into three tiers by provenance. A single `evals/datasets/registry.yaml`
manifest records for each dataset: `id`, `source_url`, `license`, `phase`,
`skill_id`, `adapter`, `checksum`, `contamination_risk`, `n_cases`.

### 3.1 Tier A — external public benchmarks (fast, citable, contamination-prone)

| Dataset | Use | License note | Contamination |
| :--- | :--- | :--- | :--- |
| [OWASP Benchmark v1.2](https://owasp.org/www-project-benchmark/) | SAST triage TP/FP; ground truth = `expectedresults-1.2.csv` | Apache-2.0-ish, redistributable | **High** — public, likely in training data |
| [D2A](https://github.com/ibm/D2A) | static-analysis TP/FP via CVE-fix differential | check IBM terms before vendoring | High |
| [SastBench](https://arxiv.org/html/2601.02941v1) | agentic SAST triage, real CVEs = TP | verify on release | Med |
| [TM-Bench](https://www.tmbench.com/methodology) | STRIDE threat-model ground truth (JSON) | verify | Med/High |
| [ThreatModeling-LLM](https://arxiv.org/html/2411.17058v2) | banking threat models + NIST 800-53 mitigations | academic | Med |
| SecReq (510 reqs, 187 security) | requirement security-relevance | academic, widely redistributed | High |
| PROMISE-NFR | non-functional/security req classification | public | High |

**Rule:** Tier A gives us fast, quotable numbers ("X% triage accuracy on OWASP
Benchmark") but every Tier A score **must be reported with a contamination caveat**
and paired with a Tier C hold-out number.

### 3.2 Tier B — real inputs, no labels (we annotate)

- [juliocesarfort/public-pentesting-reports](https://github.com/juliocesarfort/public-pentesting-reports)
  and [reconmap/pentest-reports](https://github.com/reconmap/pentest-reports):
  real, already-redacted pentest reports → excellent *inputs* for the Testing/
  Operations phases, but **carry no evaluation labels**. Annotate a subset (§3.3).
- Open-source project design docs / RFCs / architecture ADRs → inputs for the
  Design phase.

### 3.3 Tier C — self-built golden set (the differentiator)

The moat. **No public dataset pairs enterprise-style documents with an expert's
assessment conclusions** for architecture review, deployment config review, or
compliance-gap analysis. Building even a small, well-annotated, *held-out* set:

1. gives us an uncontaminated number to anchor credibility, and
2. if open-sourced, positions DocSentinel as the party that **defines the benchmark**
   for this space — competitors then have to score on our set.

**Build protocol (document it publicly for reproducibility):**

- **Size:** start 20–30 cases across phases; grow to ~50. Small-but-clean beats large-but-noisy.
- **Inputs:** redacted real docs (Tier B) + synthetic-but-realistic docs authored for
  the eval. Never commit un-redacted client material — see §7.
- **Annotation:** ≥2 senior security engineers independently produce the expected
  item set (risks/threats/gaps) using the **same vocabulary as the report schema**
  (§4). Reconcile disagreements; record **inter-annotator agreement** (this is the
  empirical ceiling on achievable F1 — a model can't beat human-human agreement).
- **Hold-out:** keep a private slice that is *never* published, to detect future
  contamination and vendor overfitting.

---

## 4. Unified Case Format

Every dataset is normalized by an **adapter** into one `EvalCase` (JSONL), so the
runner and scorers are dataset-agnostic. Ground truth is expressed in the **same
vocabulary as `docs/schemas/assessment-report.json`** so matching is apples-to-apples.

```jsonc
// evals/cases/<dataset_id>/<case_id>.json
{
  "case_id": "tmbench-0007",
  "dataset_id": "tmbench",
  "phase": "design",                 // maps to submit(phase=...)
  "skill_id": "ssdlc-design",        // maps to submit(skill_id=...)
  "inputs": [                        // -> parsed into list[ParsedDocument]
    { "path": "inputs/tmbench-0007.md", "type": "markdown" }
  ],
  "ground_truth": {
    "threats":        [ { "component": "...", "stride": "S", "description": "..." } ],
    "risk_items":     [ { "severity": "high", "description": "..." } ],
    "compliance_gaps":[ { "framework": "GDPR", "control_or_clause": "Art.32", "gap_description": "..." } ],
    "vulnerabilities":[ { "cwe": "CWE-89", "label": "true_positive" } ]
  },
  "meta": { "license": "...", "contamination_risk": "high", "annotators": 2, "iaa": 0.71 }
}
```

Adapters live in `evals/adapters/<dataset_id>.py`, each exposing
`def to_cases(raw_dir: Path) -> Iterable[EvalCase]`.

---

## 5. Matching and Scoring (the crux)

Predicted items are free text; ground-truth items are free text. Scoring hinges on
**aligning** them. Use a **three-stage cascade**, most deterministic first:

1. **Hard key match.** When a stable key exists, match on it exactly:
   CWE id (SAST), STRIDE category + component (threat model), requirement id.
2. **Semantic match.** For remaining unmatched pairs, compute embedding cosine
   similarity between descriptions; accept above a tuned threshold `τ`. `τ` is
   calibrated once against human judgments and frozen per release.
3. **LLM-as-judge adjudication.** For borderline pairs (near `τ`), ask a judge model
   "does predicted item P describe the same finding as ground-truth item G?" with a
   rubric, returning `{same: bool, rationale: str}`.

Then compute a **maximum-weight bipartite matching** (Hungarian) over the pairwise
match scores to get a 1:1 alignment; unmatched predictions = false positives,
unmatched ground truth = false negatives.

### 5.1 Judge reliability (mandatory guardrails)

The judge is itself under test. Required controls:

- **Different family than the system under test.** If DocSentinel is run on Claude,
  judge with a non-Claude model (and vice-versa); run the whole matrix (§6) so no
  single model is both author and judge on the headline number.
- **Log every rationale.** Judge decisions are auditable artifacts.
- **Human audit.** Sample ≥50 judge decisions per release; a human labels them;
  report **Cohen's κ (judge vs human)**. If κ < 0.6, the judge stage is not trusted
  and results are flagged provisional.
- **Position/verbosity bias:** randomize P/G order; strip severity/confidence from
  the judge prompt so it can't anchor on them.

---

## 6. Runner and Model Matrix

`AssessmentService.submit()` (`app/services/assessment_service.py`) accepts an
injectable `runner` and returns a task; `wait_for_terminal()` + `get()` return the
structured report. The harness uses this directly — **no HTTP, no UI**.

```python
# evals/runner/run_eval.py  (sketch — Codex to implement)
async def run_case(case: EvalCase, cfg: RunConfig) -> AssessmentReport:
    docs = parse_inputs(case.inputs)                 # -> list[ParsedDocument]
    svc = AssessmentService()
    created = await svc.submit(
        docs, phase=case.phase, skill_id=case.skill_id,
        collaborative_mode=cfg.collaborative, source="eval",
    )
    result = await svc.wait_for_terminal(str(created.task_id))
    return result.report
```

**Determinism:** temperature 0, fixed seed where the provider supports it, pinned
model ids. Run each case `N≥3` times regardless (LLMs are not bit-deterministic).

**Model matrix** (`evals/configs/matrix.yaml`): run every dataset across at least
`{ollama-local, one hosted GPT-class, one hosted Claude-class}`. This separates
*pipeline quality* (prompts, graph, RAG) from *base-model quality*, and gives the
air-gapped/local story its own honest number (local models will score lower — say so).

---

## 7. Repository Layout

```
evals/
  README.md                 # how to run, how to read scorecards
  registry.yaml             # dataset manifest (source, license, checksum, contamination)
  configs/
    matrix.yaml             # provider/model matrix + run params (N, temperature)
  datasets/                 # vendored raw data OR fetch scripts (respect licenses!)
    <dataset_id>/ ...
  adapters/
    <dataset_id>.py         # raw -> EvalCase
  cases/                    # normalized EvalCase JSONL (committed, small)
  runner/
    run_eval.py             # orchestrates: cases x matrix -> raw reports
    parse.py                # inputs -> list[ParsedDocument]
  scoring/
    matcher.py              # 3-stage cascade + Hungarian alignment
    judge.py                # LLM-as-judge with rubric + bias guards
    scorers/
      set_detection.py      # P/R/F1 for risks/threats/gaps
      triage.py             # binary TP/FP + FP-rate
      classification.py     # requirements
      grounding.py          # citation attribution / hallucination
      calibration.py        # ECE
  reports/
    <run_id>/scorecard.json # machine-readable
    <run_id>/scorecard.md   # human-readable, per skill/phase + variance
  tests/                    # unit tests for adapters, matcher, scorers
```

**Data hygiene (hard rule):** never commit un-redacted client documents. Tier C
inputs are either synthetic or already-public-redacted. Add a pre-commit check
(`evals/tests/test_no_secrets.py`) that scans committed inputs for obvious PII/secrets.

---

## 8. Milestones (Codex-executable)

Each milestone has a definition of done Codex can verify.

- **M0 — Scaffolding.** Create `evals/` layout, `registry.yaml`, `EvalCase`
  pydantic model, `RunConfig`. *DoD:* `pytest evals/tests` runs (empty green);
  `EvalCase` round-trips the example in §4.
- **M1 — Runner over one dataset.** Implement `run_eval.py` + `parse.py`; wire the
  SAST-triage path against **OWASP Benchmark** (Tier A, hard-key match, no judge
  needed). *DoD:* produces `scorecard.json` with accuracy/precision/recall/**FP-rate**
  for one model; numbers stable across two invocations (±0 on hard-key match).
- **M2 — Set-detection scorer + matcher.** Implement 3-stage matcher (start with
  stages 1–2, embeddings only) + `set_detection.py`; wire **TM-Bench** (threat
  modeling). *DoD:* P/R/F1 with severity breakdown + variance across N=3.
- **M3 — LLM-as-judge + reliability.** Add judge stage, rationale logging, the
  human-audit sampler, and κ computation. *DoD:* κ reported on a hand-labeled
  sample; results flagged provisional if κ<0.6.
- **M4 — Golden set (Tier C).** Land 20–30 annotated cases (design/deploy/compliance)
  with IAA recorded; wire `risk_items` + `compliance_gaps` scoring. *DoD:* held-out
  slice exists and is git-ignored from the public set; IAA in `meta`.
- **M5 — Grounding + calibration.** Implement `grounding.py` (citation attribution,
  hallucination rate) and `calibration.py` (ECE). *DoD:* both appear in scorecard.
- **M6 — Model matrix + published scorecard.** Run the full matrix; generate the
  human-readable `scorecard.md` (per skill/phase, mean±std, contamination caveats,
  judge-κ). *DoD:* one command reproduces the published numbers from a clean checkout.
- **M7 — CI regression gate.** A fast subset (hard-key datasets, single model, N=1)
  runs on PRs; fails if headline F1 drops > threshold vs baseline. *DoD:* green on
  main, and a deliberately-broken prompt makes it red.

---

## 9. CI Integration

- **Full eval:** manual / nightly (cost + latency make it unfit for every PR).
- **Regression subset:** deterministic, cheap (OWASP-Benchmark hard-key path + a
  handful of golden cases, single local model, N=1). Gate on **severity-weighted
  recall** regression, not just mean F1 — a change that trades a critical-risk catch
  for two low-risk catches must fail.
- Baselines stored under `evals/reports/baselines/`; the gate diffs against them.

---

## 10. Open Problems (state them; don't paper over them)

1. **Contamination.** OWASP Benchmark, SecReq, and public pentest reports are almost
   certainly in frontier-model training data. Tier A numbers are optimistic. Mitigate
   with the Tier C hold-out and, optionally, perturbed variants of Tier A inputs.
2. **Ground-truth subjectivity.** Two senior engineers disagree on risk sets. IAA is
   the real ceiling; report it and don't claim F1 above it as "superhuman."
3. **Judge reliability.** LLM-as-judge can be biased and can collude with same-family
   authors. §5.1 guards reduce but don't eliminate this; κ-vs-human is the honesty check.
4. **Severity is fuzzy.** "high" vs "medium" is itself a judgment. Consider scoring
   with a tolerance band (±1 severity level) and reporting both strict and lenient.
5. **Cross-phase items.** `cross_phase_refs` (a design risk resurfacing in testing) has
   no clean ground truth yet — deferred beyond M7.

---

## 11. References

- OWASP Benchmark — https://owasp.org/www-project-benchmark/
- D2A dataset — https://github.com/ibm/D2A
- SastBench — https://arxiv.org/html/2601.02941v1
- TM-Bench — https://www.tmbench.com/methodology
- ThreatModeling-LLM — https://arxiv.org/html/2411.17058v2
- LINDDUN GO multi-agent benchmark — https://www.sciencedirect.com/science/article/abs/pii/S2214212626001195
- SecReq / PROMISE-NFR requirements classification — https://arxiv.org/html/2509.13868
- public-pentesting-reports — https://github.com/juliocesarfort/public-pentesting-reports
- A Practical Guide for Evaluating LLMs and LLM-Reliant Systems — https://arxiv.org/html/2506.13023v1
