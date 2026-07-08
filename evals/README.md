# DocSentinel Evaluations

This directory contains the reproducible evaluation harness described in
`docs/07-evaluation-plan.md`.

Current scope:

- **M0**: evaluation layout, `EvalCase`, `RunConfig`, and dataset registry.
- **M1**: OWASP Benchmark SAST triage adapter, direct `AssessmentService` runner,
  hard-key CWE triage scoring, and scorecard outputs.

Raw datasets are not committed. Use the dataset-specific fetch script to download
public data into ignored local paths.

```bash
python evals/datasets/owasp_benchmark/fetch.py
python -m evals.runner.run_eval \
  --dataset-id owasp_benchmark \
  --raw-dir evals/datasets/owasp_benchmark/raw/BenchmarkJava-master \
  --run-id local-owasp \
  --repeats 1
```

The runner writes:

- `evals/reports/<run_id>/scorecard.json`
- `evals/reports/<run_id>/scorecard.md`

M1 uses deterministic hard-key CWE triage scoring and does not use an LLM judge.

