# Six-Phase Synthetic SSDLC Golden Set v1

This small offline dataset exercises DocSentinel's requirements, design,
development, testing, deployment, and operations skills. Every organization,
system, artifact, and finding is fictional. The files contain no copied client
material, production secrets, or third-party benchmark records and are covered
by the repository's MIT license.

Each source statement has a stable locator such as `REQ-02` or `DEP-03`.
`cases.jsonl` records expected risks, severity, project-local policy controls,
and supporting locators. `manifest.json` pins every committed data file by
SHA-256 so an evaluation cannot silently run against modified ground truth.

Important review boundary: these AI-assisted fixtures are intentionally marked
`not_expert_reviewed`. They are a contestable starter set and a deterministic
scorer/CI contract, not an expert-approved security baseline. The committed
oracle scorecard proves the harness can recover known truth; it is not model
performance. Maintainers should review and revise findings before promoting a
future baseline to `approved`.

Run an actual pipeline evaluation with:

```bash
python -m evals.runner.run_eval \
  --dataset-id ssdlc_synthetic_v1 \
  --raw-dir evals/datasets/ssdlc_synthetic_v1 \
  --run-id local-six-phase \
  --repeats 1
```

The scorer is deterministic: exact IDs match first; otherwise at least 60% of
an expected finding's declared terms must appear in the prediction. It then
reports risk and compliance-gap precision/recall/F1 plus severity, policy
mapping, evidence-locator, and schema fidelity on matched findings.
