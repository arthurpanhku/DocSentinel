# ADR-001: Modular Monolith and Persistent State

- Status: Accepted
- Date: 2026-06-25

## Context

The current application combines API handlers, task state, orchestration, and
storage concerns. Assessment tasks are held in process memory, while the
architecture documentation describes persistent workflows that are not yet
implemented.

## Decision

DocSentinel v5 will remain one deployable application while enforcing these
module boundaries:

```text
app/
  domain/
  application/
  workflows/
  infrastructure/
  interfaces/
```

- PostgreSQL is the system of record.
- Alembic owns schema migrations.
- Vector and graph indexes are derived data and can be rebuilt.
- Local filesystem storage is the default document backend.
- Redis and a worker process provide durable background execution.
- LangGraph may coordinate recoverable workflow state, but business rules
  remain in domain/application services.
- FastAPI and MCP adapt external requests into application use cases.

## Consequences

- API handlers stop mutating module-level dictionaries.
- Singleton services are replaced by explicit application dependencies.
- A service restart cannot lose assessment, review, or remediation state.
- Module contracts can later be extracted into services if deployment scale
  requires it.

## Migration Rule

New v5 functionality is implemented in the target modules. Existing v1
endpoints remain as adapters until the corresponding v2 workflow is complete.
