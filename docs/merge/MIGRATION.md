# PallasGuard Merge Migration Guide

This guide covers upgrades from pre-merge DocSentinel to the merged
DocSentinel + PallasGuard governance platform.

## What Changed

- LangChain/LangGraph dependencies now target the 1.x generation used by the
  merged agent graph.
- Alembic is now present and owns the governance schema migration history.
- Governance APIs and the React governance portal use JWT login against the
  existing `User` model.
- Policy packs live in `policy_packs/` and default to `generic-ssdlc` with
  public framework overlays.
- Optional Postgres, Redis, and Prometheus-style metrics are disabled by
  default and only enabled through environment or Compose profile settings.

## New Environment Variables

Add these to deployments that maintain their own `.env` or secret store:

```bash
AGENT_LLM_MODE=
ANTHROPIC_AUTH_TOKEN=
LLM_CONFIG_FILE=./llm_config.json
POLICY_PACK_ID=generic-ssdlc
POLICY_PACKS_DIR=./policy_packs
POLICY_PACKS_OVERLAY_DIR=
REDIS_URL=
ENABLE_METRICS=false
```

Existing database and local-account variables remain supported:

```bash
DATABASE_URL=sqlite:///./database.db
ENABLE_CREATE_ALL=true
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_CLIENT_EMAIL=client@example.com
INITIAL_SECURITY_EMAIL=security@example.com
INITIAL_APPROVER_EMAIL=approver@example.com
```

Passwords are intentionally empty by default. Create users through your normal
provisioning path or seed them only from a trusted deployment secret source.

## Fresh Install

1. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install frontend dependencies and build the console:

   ```bash
   cd frontend
   npm ci
   npm run build
   cd ..
   ```

3. Apply database migrations:

   ```bash
   alembic upgrade head
   ```

4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

## Existing SQLite Development Database

Older DocSentinel development databases may have been created with
`SQLModel.create_all()` and may not contain an `alembic_version` table.

1. Back up the database:

   ```bash
   cp database.db database.db.pre-pallasguard-merge
   ```

2. Let SQLModel create any missing governance tables in local development:

   ```bash
   ENABLE_CREATE_ALL=true uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

3. Stop the server after startup completes, then stamp the current schema:

   ```bash
   alembic stamp head
   ```

For production or shared environments, prefer a fresh migrated database or a
reviewed manual migration instead of relying on `create_all`.

## New Tables

The first governance migration creates or manages these tables:

- `auditlog`
- `user`
- `governance_audit_logs`
- `org_framework_configs`
- `policy_documents`
- `projects`
- `compliance_obligations`
- `control_instances`
- `gate_submissions`
- `policy_embeddings`
- `prompt_audit_logs`
- `questionnaire_instances`
- `sub_agent_runs`
- `control_evidence_items`
- `question_instances`
- `requirement_rows`
- `evidence_items`

## Docker

The default Compose profile remains lightweight:

```bash
docker compose up -d
```

The optional full profile starts Postgres and Redis in addition to the app:

```bash
docker compose --profile full up -d
```

The app does not require Redis or Prometheus metrics unless `REDIS_URL` or
`ENABLE_METRICS=true` is set.

## Rollback

Each merge phase is a standalone commit with a `[mergeP{n}]` prefix. To revert a
specific phase, use `git revert <phase-commit>`, then rerun the phase acceptance
commands before continuing.
