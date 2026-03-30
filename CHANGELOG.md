# Changelog

All notable changes to DocSentinel are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [4.0.0] — 2026-03-29

### Added
- **SSDLC Pipeline**: Full Secure Software Development Lifecycle support with 6 stage-specific assessment flows:
  - **Requirements**: Security requirements completeness, compliance mapping, risk analysis.
  - **Design**: Architecture security review, STRIDE/DREAD threat modeling, encryption/permission design.
  - **Development**: Secure coding standards, anti-injection/XSS controls verification.
  - **Testing**: SAST/DAST report triage, penetration test findings evaluation, vulnerability verification.
  - **Deployment**: Release readiness review, configuration security, key management, hardening.
  - **Operations**: Vulnerability monitoring, incident response evaluation, patch management, log audit.
- **SSDLC Stage Skills**: 6 built-in stage-specific skills with tailored system prompts, risk focus areas, and compliance framework mappings.
- **SSDLC Auto-detection**: Router node can auto-detect the SSDLC stage from document content when not explicitly specified.

### Changed
- **LangGraph Orchestrator**: Replaced custom `asyncio.gather` orchestration with **LangChain + LangGraph** stateful graph-based agent workflows. Graph nodes: Parser → SSDLC Router → Policy+Evidence (parallel fan-out) → Drafter → Reviewer.
- **Assessment API**: `POST /assessments` now accepts optional `ssdlc_stage` parameter.
- **MCP Tools**: `assess_document` tool now accepts optional `ssdlc_stage` parameter.
- **Report Schema**: Added `ssdlc_stage` field to `AssessmentReport.metadata`.

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

[4.0.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v4.0.0
[3.1.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v3.1.0
[3.0.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v3.0.0
[2.0.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v2.0.0
[0.3.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v0.3.0
[0.2.0]: https://github.com/arthurpanhku/DocSentinel/releases/tag/v0.2.0
