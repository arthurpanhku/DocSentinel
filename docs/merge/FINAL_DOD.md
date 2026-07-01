# Final Definition of Done

Date: 2026-07-01
Branch: `feat/pallasguard-merge`

## Invariants

- [x] DocSentinel original capabilities remain available: Docling parser,
  ChromaDB + LightRAG, MCP server, A2A gateway, multi-provider LLM routing, and
  six-stage SSDLC assessments are covered by the existing test suite and build.
- [x] PallasGuard governance capabilities are available: policy-pack SCD
  controls, Gate 1/3 workflow data structures, submissions, approvals, audit
  trails, Pallas Lens scoring, and eight public compliance overlays.
- [x] The platform converges on one LLM abstraction, LangGraph orchestration,
  and SQLModel/Alembic persistence.
- [x] `pytest -q` passes.
- [x] `cd frontend && npm run build` passes.
- [x] `docker compose up -d --build` starts the default app profile and
  `/health` returns `{"status":"ok"}`.
- [x] `docker compose --profile full up -d` starts app, Postgres, and Redis;
  Postgres and Redis health checks reach `healthy`.
- [x] `pre-commit run --all-files` passes.
- [x] Sensitive-content grep has zero matches.

## Final Commands

```bash
.venv/bin/pytest -q
cd frontend && npm run build
docker compose up -d --build
docker compose --profile full up -d
pre-commit run --all-files
required sensitive-content grep from the merge plan
```

Detailed command outputs are tracked in the Phase 7 commit body.
