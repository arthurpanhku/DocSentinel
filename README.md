<div align="center">

[English](README.md) | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md) | [Deutsch](README_de.md)

</div>

<p align="center">
  <img src="docs/images/docsentinel-mascot.png" width="200" alt="DocSentinel mascot"/>
</p>

<p align="center">
  <strong>DocSentinel</strong><br/>
  <em>AI-powered SSDLC security assessment for documents and questionnaires</em>
</p>

<p align="center">
  <a href="https://github.com/arthurpanhku/DocSentinel/releases"><img src="https://img.shields.io/github/v/release/arthurpanhku/DocSentinel?include_prereleases" alt="Latest release"/></a>
  <a href="https://github.com/arthurpanhku/DocSentinel/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"/></a>
  <a href="https://github.com/arthurpanhku/DocSentinel"><img src="https://img.shields.io/badge/GitHub-arthurpanhku%2FDocSentinel--Agent-24292e?logo=github" alt="GitHub repo"/></a>
  <a href="docs/06-agent-integration.md"><img src="https://img.shields.io/badge/MCP-Ready-green?logo=anthropic" alt="MCP Ready"/></a>
  <a href="docs/06-agent-integration.md"><img src="https://img.shields.io/badge/Agent-Integration-blueviolet" alt="Agent Integration"/></a>
</p>

<p align="center">
  <a href="https://glama.ai/mcp/servers/arthurpanhku/DocSentinel">
    <img width="380" height="200" src="https://glama.ai/mcp/servers/arthurpanhku/DocSentinel/badge" />
  </a>
</p>

---

## What is DocSentinel?

**DocSentinel** is an AI-powered assistant for security teams. It automates the review of security-related **documents, forms, and reports** across the **entire Secure Software Development Lifecycle (SSDLC)** — from requirements and design through development, testing, deployment, and operations. It compares inputs against your policy and knowledge base, and produces **structured assessment reports** with risks, compliance gaps, and remediation suggestions.

🚀 **Agent Ready**: Supports **Model Context Protocol (MCP)** to be used as a "skill" by OpenClaw, Claude Desktop, and other autonomous agents.

- **SSDLC lifecycle coverage**: 6 stages (Requirements, Design, Development, Testing, Deployment, Operations) with stage-specific skills and checklists.
- **LangGraph orchestration**: Stateful, graph-based agent workflows with conditional branching per SSDLC stage.
- **Multi-format input**: PDF, Word, Excel, PPT, text — parsed into a unified format for the LLM.
- **Knowledge base (RAG)**: Upload policy and compliance documents; the agent uses them as reference when assessing.
- **Multiple LLMs**: Use OpenAI, Claude, Qwen, or **Ollama** (local) via a single interface.
- **Structured output**: JSON/Markdown reports with risk items, compliance gaps, and actionable remediations.

Ideal for enterprises that need to scale security assessments across many projects and SSDLC stages without proportionally scaling headcount.

---

## Why DocSentinel?

| Pain Point                                                                                                                    | DocSentinel Solution                                                                         |
| :---------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| **Fragmented criteria**<br>Policies, standards, and precedents are scattered.                                                 | Single **knowledge base** ensures consistent findings and traceability.                      |
| **Heavy questionnaire workflow**<br>Business fills form → Security reviews → Business adds evidence → Security reviews again. | **Automated first-pass** and gap analysis reduces manual back-and-forth rounds.              |
| **Pre-release review pressure**<br>Security needs to review and sign off on technical docs before launch.                     | **Structured reports** help reviewers focus on decision-making, not line-by-line reading.    |
| **Scale vs. consistency**<br>Many projects and standards lead to inconsistent or delayed manual reviews.                      | **Unified pipeline** with configurable scenarios keeps assessments consistent and auditable. |
| **SSDLC coverage gaps**<br>Security involvement is uneven across lifecycle stages; early stages get less scrutiny.            | **Stage-aware assessment** covers all 6 SSDLC stages with dedicated skills and checklists.  |

*See the full problem statement and product goals in [SPEC.md](./SPEC.md).*

---

## Architecture

DocSentinel is built around a **LangGraph orchestrator** that coordinates parsing, SSDLC stage routing, the knowledge base (RAG), skills, and the LLM. You can use cloud or local LLMs and optional integrations (e.g. AAD, ServiceNow) as your environment requires.

```mermaid
flowchart TB
    subgraph User["👤 User / Security Staff"]
    end
    subgraph Access["Access Layer"]
        API["REST API / MCP"]
    end
    subgraph Core["DocSentinel Core"]
        Orch["LangGraph\nOrchestrator"]
        SSDLC["SSDLC Pipeline\n(6 stages)"]
        Mem["Memory"]
        Skill["Skills"]
        KB["Knowledge Base (RAG)"]
        Parser["Parser"]
    end
    subgraph LLM["LLM Layer"]
        Abst["LLM Abstraction\n(LangChain)"]
    end
    subgraph Backends["LLM Backends"]
        Cloud["OpenAI / Claude / Qwen"]
        Local["Ollama / vLLM"]
    end

    User --> API
    API --> Orch
    Orch --> SSDLC
    SSDLC --> Skill
    Orch <--> Mem
    Orch --> KB
    Orch --> Parser
    Orch --> Abst
    Abst --> Cloud
    Abst --> Local
```

**Data flow (simplified):**

1.  User uploads documents and optionally specifies SSDLC stage.
2.  **Parser** converts files (PDF, Word, Excel, PPT, etc.) to text/Markdown.
3.  **SSDLC Router** determines lifecycle stage and loads stage-specific skill + checklist.
4.  **LangGraph** runs the agent graph: Policy+Evidence in parallel, then Drafter+Reviewer.
5.  Returns **assessment report** (risks, gaps, remediations, confidence, SSDLC stage).

*Detailed architecture: [ARCHITECTURE.md](./ARCHITECTURE.md) and [docs/01-architecture-and-tech-stack.md](./docs/01-architecture-and-tech-stack.md).*

---

## ✨ Core Capabilities

### 🔄 Full SSDLC Lifecycle Coverage
Assess documents at every stage of the Secure Software Development Lifecycle:
- **Requirements**: Security requirements, compliance mapping, initial risk analysis.
- **Design**: Architecture review, STRIDE/DREAD threat modeling, SDR.
- **Development**: Secure coding standards, code review findings.
- **Testing**: SAST/DAST report triage, pen-test evaluation.
- **Deployment**: Release readiness, config security, hardening.
- **Operations**: Incident response, vulnerability monitoring, log audit.

### 🛡️ Automated Security Assessment
Submit security questionnaires, design documents, or audit reports. DocSentinel analyzes them using configured LLMs and identifies:
- **Security Risks**: Classified by severity (Critical, High, Medium, Low).
- **Compliance Gaps**: Missing controls against frameworks like ISO 27001, PCI DSS.
- **Remediation Steps**: Actionable advice to fix identified issues.

### 🧠 RAG-Powered Knowledge Base
Upload your organization's internal security policies, standards, and past audits. The agent indexes these documents to provide **context-aware assessments**, citing specific policy clauses in its findings.

### 🔗 LangGraph Agent Orchestration
Powered by **LangChain + LangGraph** — stateful, graph-based agent workflows with conditional routing per SSDLC stage. Parallel execution of Policy and Evidence agents, followed by Drafter and Reviewer agents.

### 🔌 API-First & MCP Ready
Designed as a headless service. Integrate it into your CI/CD pipelines via REST API, or use it as a **super-tool** within AI agents (like Claude Desktop, OpenClaw) using the Model Context Protocol (MCP).

---

## 🤖 Agent Integration (MCP)

Connect DocSentinel to **Claude Desktop**, **Cursor**, or **OpenClaw** to use it as a powerful security skill.

### 💡 What can it do?
Once connected, you can ask your AI agent:
> "Read the attached `system-design.pdf` and assess it for compliance risks using DocSentinel."
>
> "Check `api-spec.yaml` against our internal `access-control-policy.pdf` in the Knowledge Base."

### 🛠️ Configuration Guide

#### 1. Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "docsentinel": {
      "command": "/path/to/DocSentinel/.venv/bin/python",
      "args": ["/path/to/DocSentinel/app/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "CHROMA_PERSIST_DIR": "/absolute/path/to/data/chroma"
      }
    }
  }
}
```

#### 2. Cursor
1. Go to **Settings > Features > MCP**.
2. Click **+ Add New MCP Server**.
   - **Name**: `docsentinel`
   - **Type**: `stdio`
   - **Command**: `/path/to/DocSentinel/.venv/bin/python`
   - **Args**: `/path/to/DocSentinel/app/mcp_server.py`

*See full guide in [docs/06-agent-integration.md](docs/06-agent-integration.md).*

---

## Quick Start

### Option A: One-Click Deployment (Recommended)

Run the deployment script to start the full stack (API + Vector DB + optional Ollama).

```bash
git clone https://github.com/arthurpanhku/DocSentinel.git
cd DocSentinel
chmod +x deploy.sh
./deploy.sh
```

-   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option B: Docker Manual

**Prerequisites**: **Python 3.10+**. Optional: [Ollama](https://ollama.ai) (`ollama pull llama2`).

```bash
git clone https://github.com/arthurpanhku/DocSentinel.git
cd DocSentinel
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit if needed: LLM_PROVIDER=ollama or openai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

-   **API docs**: [http://localhost:8000/docs](http://localhost:8000/docs) · **Health**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Example: submit an assessment

You can use the sample files in [examples/](examples/) to try the API.

```bash
# Use sample file from repo
curl -X POST "http://localhost:8000/api/v1/assessments" \
  -F "files=@examples/sample.txt" \
  -F "scenario_id=default"

# Response: { "task_id": "...", "status": "accepted" }
# Get the result (replace TASK_ID with the returned task_id)
curl "http://localhost:8000/api/v1/assessments/TASK_ID"
```

### Example: upload to KB and query

```bash
# Use sample policy from repo
curl -X POST "http://localhost:8000/api/v1/kb/documents" -F "file=@examples/sample-policy.txt"

# Query the KB (RAG)
curl -X POST "http://localhost:8000/api/v1/kb/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the access control requirements?", "top_k": 5}'
```

---

## Hosted deployment

A hosted deployment is available on [Fronteir AI](https://fronteir.ai/mcp/arthurpanhku-docsentinel).

## Project layout

```text
DocSentinel/
├── app/                  # Application code
│   ├── api/              # REST routes: assessments, KB, health, skills
│   ├── agent/            # LangGraph orchestrator, skills registry & service
│   │   └── ssdlc/        # SSDLC pipeline: stage router, stage skills, checklists
│   ├── core/             # Config, guardrails, security, DB
│   ├── kb/               # Knowledge Base (Chroma + LightRAG graph RAG)
│   ├── llm/              # LLM abstraction (OpenAI, Ollama)
│   ├── parser/           # Document parsing (Docling + legacy fallback)
│   ├── models/           # Pydantic / SQLModel models
│   ├── main.py           # FastAPI app entry point
│   └── mcp_server.py     # MCP Server for agent integration
├── tests/                # Automated tests (pytest)
├── examples/             # Sample files (questionnaires, policies)
├── docs/                 # Design & Spec documentation
│   ├── 01-architecture-and-tech-stack.md
│   ├── 02-api-specification.yaml
│   ├── 03-assessment-report-and-skill-contract.md
│   ├── 04-integration-guide.md
│   ├── 05-deployment-runbook.md
│   └── schemas/
├── .github/              # Issue/PR templates, CI (Actions)
├── Dockerfile
├── docker-compose.yml    # API only
├── docker-compose.ollama.yml  # API + Ollama optional
├── CONTRIBUTING.md       # Contribution guidelines
├── CODE_OF_CONDUCT.md    # Code of conduct
├── CHANGELOG.md
├── SPEC.md
├── LICENSE
├── SECURITY.md
├── requirements.txt
├── requirements-dev.txt  # Dev dependencies
└── .env.example
```

---

## Configuration

| Variable                                       | Description                            | Default                             |
| :--------------------------------------------- | :------------------------------------- | :---------------------------------- |
| `LLM_PROVIDER`                                 | `ollama` or `openai`                   | `ollama`                            |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL`             | Local LLM                              | `http://localhost:11434` / `llama2` |
| `OPENAI_API_KEY` / `OPENAI_MODEL`              | OpenAI                                 | —                                   |
| `CHROMA_PERSIST_DIR`                           | Vector DB path                          | `./data/chroma`                     |
| `PARSER_ENGINE`                                | Parser: `auto`, `docling`, or `legacy` | `auto`                              |
| `ENABLE_GRAPH_RAG`                             | Enable LightRAG graph retrieval         | `true`                              |
| `SSDLC_DEFAULT_STAGE`                          | Default SSDLC stage if not specified    | `auto`                              |
| `UPLOAD_MAX_FILE_SIZE_MB` / `UPLOAD_MAX_FILES` | Upload limits                          | `50` / `10`                         |

*See [.env.example](./.env.example) and [docs/05-deployment-runbook.md](./docs/05-deployment-runbook.md) for full options.*

---

## Documentation and PRD

-   **[ARCHITECTURE.md](./ARCHITECTURE.md)** — System architecture: high-level diagram, Mermaid views, component design, data flow, security.
-   **[SPEC.md](./SPEC.md)** — Product requirements: problem statement, solution, features, security controls.
-   **[CHANGELOG.md](./CHANGELOG.md)** — Version history; [Releases](https://github.com/arthurpanhku/DocSentinel/releases).
-   **Design docs** [docs/](./docs/)：Architecture, API spec (OpenAPI), contracts, integration guides (AAD, ServiceNow), deployment runbook. Q1 Launch Checklist: [docs/LAUNCH-CHECKLIST.md](./docs/LAUNCH-CHECKLIST.md).

---

## Development & Testing

To verify your installation or contribute to the project, run the test suite:

### Option A: One-Click Test (Recommended)
Automatically sets up a test environment and runs all checks.

```bash
chmod +x test_integration.sh
./test_integration.sh
```

### Option B: Manual
```bash
# 1. Install dev dependencies
pip install -r requirements-dev.txt

# 2. Run all tests
pytest

# 3. Run specific test (e.g. Skills API)
pytest tests/test_skills_api.py
```

## Contributing

Issues and Pull Requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, and commit guidelines. By participating you agree to the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

🤖 **AI-Assisted Contribution**: We encourage using AI tools to contribute! Check out [CONTRIBUTING_WITH_AI.md](CONTRIBUTING_WITH_AI.md) for best practices.

📜 **Submit a Skill Template**: Have a great security persona? Submit a [Skill Template](https://github.com/arthurpanhku/DocSentinel/issues/new?template=new_skill_template.md) or add it to `examples/templates/`. We welcome real-world (sanitized) security questionnaires to improve our templates!

---

## Security

-   **Vulnerability reporting**: See [SECURITY.md](./SECURITY.md) for responsible disclosure.
-   **Security requirements**: Follows security controls in [SPEC §7.2](./SPEC.md).

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=arthurpanhku/DocSentinel&type=Date)](https://star-history.com/#arthurpanhku/DocSentinel&Date)

---

## Author and links

-   **Author**: PAN CHAO (Arthur Pan)
-   **Repository**: [github.com/arthurpanhku/DocSentinel](https://github.com/arthurpanhku/DocSentinel)
-   **SPEC and design docs**: See links above.

If you use DocSentinel in your organization or contribute back, we’d love to hear from you (e.g. via GitHub Discussions or Issues).
