# Changelog

All notable changes to DocSentinel are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — PallasGuard merge

### Added
- Governance domain model and Alembic migrations for projects, submissions,
  control instances, questionnaires, audit trails, prompt audit records, and
  sub-agent runs.
- Policy-pack driven governance with `generic-ssdlc`, framework templates, and
  eight public compliance overlays: NIST SSDF, MAS TRM, ISO 27001:2022,
  EU AI Act, ISO 42001, China MLPS 2.0, OWASP SAMM, and EU CRA.
- Governance APIs for projects, controls, evidence, submissions,
  questionnaires, schema discovery, Pallas Lens scoring, sub-agent tracking,
  and JWT login.
- React governance portal with project creation, framework overlay selection,
  control evidence capture, Pallas Lens readiness scoring, and sub-agent run
  visibility.
- Excel/offline governance helpers and a single knowledge-base ingestion entry
  that writes to Chroma, Graph RAG, and the lightweight lexical knowledge graph.
- Optional Postgres/Redis Docker Compose `full` profile and opt-in
  Prometheus metrics wiring through `ENABLE_METRICS`.
- MCP Streamable HTTP and A2A 1.0 JSON-RPC agent endpoints backed by a shared
  assessment task service and visible in the Agent Integrations console.
- Loopback-only defaults, optional bearer protection, A2A Agent Card discovery,
  and protocol-level integration tests.
- Generated OpenAPI and assessment JSON Schema contracts with TypeScript client
  types derived from the FastAPI application.
- Frontend query provider, accessible mobile navigation, icon tooltips, component
  tests, and CI checks for type safety, tests, and production builds.
- v5 product trust RFC and architecture, evidence-model, and frontend-design ADRs.

### Changed
- Converged orchestration on LangGraph while keeping DocSentinel's assessment
  task lifecycle, report contracts, and existing API surface intact.
- Converged LLM access on the DocSentinel provider abstraction with
  LangChain 1.x compatible clients and Anthropic-compatible mode support.
- Moved governance additions into new modules/functions where names overlapped
  with existing DocSentinel core modules.
- Unified REST, MCP, and A2A assessment submissions behind one task lifecycle;
  agent submissions always require human review.
- Updated the assessment report model to the v2 contract, including finding-level
  evidence references, threat models, vulnerabilities, and cross-phase references.
- Moved FastAPI Swagger UI to `/api-docs` and restricted CORS to configured local
  origins by default.
- Built the React console inside the Docker image and pinned the container to
  official CPU-only PyTorch wheels for practical private deployment.

### Security
- Excluded private/local policy-pack material from the merge and retained the
  final sensitive-content grep gate in `docs/merge/EXCLUSIONS.md`.
- Added bcrypt 5 compatibility fallback for JWT password verification while
  preserving the existing passlib-first security path.
- Constrained MCP `assess_document.file_path` reads to configured `MCP_DOCUMENT_ROOTS`
  before opening files, including symlink escape protection and pre-read extension
  validation.
- Constrained knowledge-base directory reindexing to `KB_REINDEX_ROOTS` before
  initializing or reading from the knowledge base.

---

## [4.2.0] — 2026-06-03

### Added
- **React Console**: Full React + TypeScript + Vite + Tailwind CSS console hosted by FastAPI at `/console`, with Dashboard, Assessments, Knowledge Base, Skills, and Settings views.
- **LLM Runtime Configuration**: Settings UI and `/config/llm` API for selecting OpenAI, Anthropic Claude, Qwen, DeepSeek, OpenAI-compatible hosted APIs, local OpenAI-compatible APIs, and Ollama.
- **SSDLC Console Workflow**: Multi-file assessment submission with phase, project, skill, and collaborative review controls; queue filtering; report review; comments; activity; and remediation tracking.
- **Console Screenshots and Architecture Diagram**: README screenshot asset plus updated architecture diagrams showing the React Console access layer.

### Changed
- **LLM Abstraction**: Expanded provider routing beyond OpenAI/Ollama and clear cached clients when runtime configuration changes.
- **Assessment Metadata**: `POST /api/v1/assessments` now accepts optional `phase` and propagates SSDLC phase metadata into reports.
- **Built-in Skills**: Added six SSDLC stage skills for Requirements, Design, Development, Testing, Deployment, and Operations.
- **Developer Workflow**: Added Makefile targets and README instructions for installing, building, and serving the React console.

### Security
- **API Key Masking**: LLM API keys are accepted by the local FastAPI process but returned to the UI only as masked previews.

---

## [4.1.0] — 2026-04-09

### Added
- **Review Console**: Minimal human-in-the-loop review console for HITL workflows and remediation tracking. Allows reviewers to approve, reject, comment on, and track remediation status of security findings.
- **Architecture Diagram**: Embedded system architecture diagram across all READMEs, ARCHITECTURE.md, and project documentation for clearer visual overview of the platform.

### Changed
- **Documentation**: Redesigned architecture diagram for improved clarity; updated all language-specific READMEs (en, zh, ja, ko, fr, de) to include the diagram.

---

## [4.0.0] — 2026-03-30

### Major Change
This release pivots DocSentinel into an **AI-powered SSDLC (Secure Software Development Lifecycle) platform**, with full-phase coverage and intelligent agent orchestration.

### Added
- **SSDLC Full Lifecycle Support**: Six dedicated phase agents — Requirements, Design, Development, Testing, Deployment, and Operations — each with specialized skills, prompts, and knowledge base collections.
  - **Requirements**: Security requirements completeness, compliance mapping, risk analysis.
  - **Design**: Architecture security review, STRIDE/DREAD threat modeling, encryption/permission design.
  - **Development**: Secure coding standards, anti-injection/XSS controls verification.
  - **Testing**: SAST/DAST report triage, penetration test findings evaluation, vulnerability verification.
  - **Deployment**: Release readiness review, configuration security, key management, hardening.
  - **Operations**: Vulnerability monitoring, incident response evaluation, patch management, log audit.
- **LangGraph Orchestration**: Stateful graph-based workflow engine replacing the custom orchestrator. Supports conditional routing, parallel execution, checkpointing, and human-in-the-loop interrupts.
- **LangChain Integration**: Unified LLM abstraction, prompt templates, tool integration, and RAG chains via LangChain framework.
- **Threat Modeling (STRIDE/DREAD)**: Design Agent performs automated threat modeling with STRIDE categorization and DREAD risk scoring.
- **SAST/DAST Report Parsers**: Dedicated parsers for SARIF, SonarQube JSON, Checkmarx XML, Burp Suite XML, and OWASP ZAP reports.
- **Phase-specific KB Collections**: Separate knowledge base collections per SSDLC phase (`kb_requirements`, `kb_design`, `kb_development`, `kb_testing`, `kb_deployment`, `kb_operations`).
- **Cross-phase Traceability**: Findings from earlier phases automatically link to later phases (e.g. Design threats → Testing test cases → Operations monitoring rules).
- **Phase-specific Skills**: 12 built-in personas across 6 SSDLC phases (Compliance Analyst, Threat Modeler, Secure Code Reviewer, Pentest Analyst, Release Reviewer, Vulnerability Monitor, etc.).
- **SSDLC Stage Skills**: 6 built-in stage-specific skills with tailored system prompts, risk focus areas, and compliance framework mappings.
- **SSDLC Auto-detection**: Router node can auto-detect the SSDLC stage from document content when not explicitly specified.

### Changed
- **Orchestrator**: Replaced custom multi-agent pipeline with LangGraph `StateGraph` supporting conditional edges, shared state (`SSDLCState`), and persistent checkpointing. Graph nodes: Parser → SSDLC Router → Policy+Evidence (parallel fan-out) → Drafter → Reviewer.
- **Assessment Reports**: Extended schema (v2.0) with `phase` field, `ThreatModel` object, `Vulnerability` array, and `CrossPhaseRef` for cross-phase traceability.
- **Assessment API**: `POST /assessments` now accepts optional `ssdlc_stage` parameter.
- **MCP Tools**: `assess_document` tool now accepts optional `ssdlc_stage` parameter.
- **Report Schema**: Added `ssdlc_stage` field to `AssessmentReport.metadata`.
- **PRD (SPEC.md)**: Rewritten as v4.0 with full SSDLC phase definitions, LangGraph/LangChain stack, and phase-specific user stories.
- **Architecture (ARCHITECTURE.md)**: Rewritten as v4.0 with LangGraph state machine design, phase agent details, and SAST/DAST integration points.
- **All documentation**: Updated to reflect SSDLC platform positioning, LangGraph orchestration, and LangChain framework.

---

## [3.1.0] — 2026-03-29

### Added
- **Graph RAG (LightRAG)**: Hybrid retrieval combining vector similarity and entity-relationship graph for enriched context.
- **Docling Parser**: Primary document parsing engine with table/heading preservation and OCR support; legacy parsers as fallback.
- **Input Guardrails**: Prompt injection detection with regex patterns, input length limits, and automatic rejection.
- **Smart Truncation**: Text truncation at sentence/paragraph boundaries instead of arbitrary character cuts.

### Changed
- **Async Assessment Pipeline**: `POST /assessments` now returns immediately with `task_id`; processing runs as a background task.
- **Parallel Orchestration**: Policy/History KB lookup and Evidence extraction run in parallel via `asyncio.gather`.
- **Singleton KnowledgeBaseService**: Single instance shared across the application lifecycle (was re-created per request).
- **Cached LLM Client**: `get_llm()` uses `@lru_cache` — one client instance per process instead of per-call.

### Removed
- **Dead code**: Removed unused `_estimate_confidence()` function (confidence is returned by Reviewer agent).

### Fixed
- **MCP Server bug**: Fixed `await` usage on `kb.query()` call — aligned with the async KB service interface after Graph RAG integration.
- **`datetime.utcnow()` deprecation**: Replaced with `datetime.now(UTC)` across all modules (Python 3.12+ compatible).

---

## [3.0.0] — 2026-03-12

### Major Change
This release transitions DocSentinel into a **pure Headless / MCP Service**. We have removed the built-in frontend to focus entirely on API and Agent integration capabilities.

### Removed
- **Frontend**: Removed the Streamlit dashboard, Assessment Workbench, and Knowledge Base Manager UI.
- **Dependencies**: Removed `streamlit`, `plotly`, `pandas`, and related UI assets.
- **Scripts**: Removed `generate_social_preview.py` and UI-related deployment configurations.

### Changed
- **Documentation**: Updated README to highlight MCP capabilities (Claude Desktop, Cursor, OpenClaw).
- **Deployment**: Simplified `docker-compose.yml` and `deploy.sh` to deploy only the backend service.

---

## [2.0.0] — 2026-03-08

### Major Release

This release marks a significant milestone with **Skill Management**, **Templates**, **Multi-Agent Orchestration v2**, and **One-Click Deployment**.

### Added
- **Skill & Persona Management**:
  - Built-in personas: `ISO 27001 Auditor`, `AppSec Engineer`, `GDPR DPO`, `Cloud Architect`.
  - Custom skills: Create, update, delete custom personas via API and UI.
  - Skill Templates: Import standard templates (SOC2, Supplier Risk, Architecture Review) from JSON.
- **Dynamic Orchestration**:
  - Orchestrator now injects persona-specific context (System Prompt, Risk Focus) into LLM calls.
  - RAG retrieval is weighted by skill focus keywords.
- **One-Click Deployment**:
  - Added `./deploy.sh` script for zero-config setup of API, Dashboard, and Vector DB.
  - Added `./test_integration.sh` for automated environment verification.
- **Documentation**:
  - Multi-language READMEs (English, Chinese, Japanese, Korean, French, German).
  - Updated `ARCHITECTURE.md` and `SPEC.md` to reflect v2.0 features.
  - Added "Features at a Glance" with UI screenshots in README.
- **Community**:
  - Added GitHub Issue Templates for submitting new Skills.

### Changed
- **API**:
  - `POST /assessments` now accepts `skill_id` and `project_id`.
  - Updated Pydantic models to be compatible with Python 3.9+ (removed `|` union types).
- **Frontend**:
  - New "Skills Manager" page for viewing and creating personas.
  - "Assessment Workbench" now supports persona selection.

### Fixed
- Fixed `ParsedDocumentMetadata` type mismatch for text/markdown files.
- Fixed `health` endpoint missing in `main.py`.

---

## [0.3.0] — 2026-03-06

### Added
- **Citation + Confidence Scoring**:
  - Added `confidence` and `sources` fields to assessment reports.
  - Added source evidence metadata (file, page, paragraph ID, excerpt, evidence link).
- **Human-in-the-Loop Workflow**:
  - Added review states: `review_pending`, `approved`, `rejected`, `escalated`.
  - Added collaboration APIs for review actions, comments, assignee, activity timeline, and revisions.
- **History Reuse + KB Updates**:
  - Added history response indexing into a dedicated vector collection.
  - Added history reuse retrieval endpoint for similar past answers.
  - Added KB reindex API and optional background auto-sync loop.
- **Multi-Agent Orchestration (v2)**:
  - Upgraded orchestration pipeline to Policy/Evidence/Drafter/Reviewer/Confidence flow.
- **Frontend Collaboration UI**:
  - Added confidence and citation views in Assessment Workbench.
  - Added approve/reject/escalate actions, comments, activity feed, and reuse candidates.
  - Added KB reindex controls in Knowledge Base page.

### Changed
- **API Models**:
  - Extended task result model with versioning, assignee, and comments.
- **Architecture Docs**:
  - Added the new architect mascot image in architecture document.

### Fixed
- **Tests and linting**:
  - Updated and expanded assessment API tests for review/collaboration flow.
  - Passed `ruff check` and full `pytest` suite for release baseline.

---

## [0.2.0] — 2026-03-06

### Added
- **Streamlit Frontend**: A modern, interactive dashboard for managing assessments and knowledge base.
  - **Dashboard**: Visual metrics and activity charts.
  - **Assessment Workbench**: Drag-and-drop file upload, real-time progress tracking, and structured report viewing (Risks, Compliance, Remediations).
  - **Knowledge Base Manager**: UI for uploading policy documents and testing RAG retrieval.
- **Developer Experience**:
  - Added `pyproject.toml` for unified tool configuration.
  - Added `Makefile` for common development tasks (`make install`, `make test`, `make lint`).
  - Added `pre-commit` hooks for code quality assurance.
  - Integrated **Ruff** for fast linting and formatting.
- **Documentation**:
  - Updated README with frontend screenshots and demo GIF.
  - Added `DEMO-RECORD.md` guide.

### Changed
- **CI/CD**: Updated GitHub Actions workflow to include linting steps.
- **Project Structure**: Migrated `pytest.ini` to `pyproject.toml`.

[4.1.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v4.1.0
[4.0.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v4.0.0
[3.1.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v3.1.0
[3.0.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v3.0.0
[2.0.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v2.0.0
[0.3.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v0.3.0
[0.2.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v0.2.0
