# Changelog

All notable changes to Arthor Agent are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

[0.3.0]: https://github.com/arthurpanhku/Arthor-Agent/releases/tag/v0.3.0
[0.2.0]: https://github.com/arthurpanhku/Arthor-Agent/releases/tag/v0.2.0
[0.1.0]: https://github.com/arthurpanhku/Arthor-Agent/releases/tag/v0.1.0
