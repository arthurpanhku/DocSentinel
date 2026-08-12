# Synthetic prompt-injection corpus

This directory defines synthetic adversarial documents for testing whether
document content can override a trusted task or DocSentinel's deterministic
rule-engine decision.

Run the generator with:

```bash
python scripts/generate_prompt_injection_corpus.py \
  tests/fixtures/prompt_injection_corpus/manifest.json \
  .tmp/prompt-injection-corpus
```

Every sample is synthetic, contains no customer data, and is licensed under
the repository's MIT license. Generated files are test inputs, not instructions
that DocSentinel or a reviewing Agent should execute.
