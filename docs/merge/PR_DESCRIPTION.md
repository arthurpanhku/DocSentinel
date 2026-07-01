# PR: Merge PallasGuard Governance into DocSentinel

## Summary

This PR merges PallasGuard governance capabilities into DocSentinel while
preserving DocSentinel history, public assets, CI, examples, MCP/A2A gateway,
React console, and existing assessment behavior.

## Phase Commits

- `[mergeP0]` Establish merge baseline, branch, exclusions, and regression
  baseline.
- `[mergeP1]` Converge dependencies on LangChain/LangGraph 1.x.
- `[mergeP2]` Merge LLM configuration and safety support.
- `[mergeP3]` Add SQLModel governance models and Alembic schema migration.
- `[mergeP4]` Introduce governance agent graph while preserving assessment
  service contracts.
- `[mergeP5]` Merge policy packs, governance services, Pallas Lens, Excel
  helpers, knowledge-base ingestion, and governance APIs.
- `[mergeP6]` Add governance frontend, JWT login, optional metrics wiring, and
  optional Postgres/Redis Compose profile.
- `[mergeP7]` Update documentation, migration guide, environment template,
  exclusions, and final validation records.

## Validation

- Backend tests: `pytest -q`
- Frontend build: `cd frontend && npm run build`
- Docker default profile: `docker compose up -d --build`
- Docker full profile: `docker compose --profile full up -d`
- Sensitive-content grep: zero matches
- Pre-commit: `pre-commit run --all-files`

## Rollback

Each phase is intentionally isolated. If a regression appears, revert the
matching `[mergeP{n}]` commit and rerun that phase's acceptance commands before
continuing.
