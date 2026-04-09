# System Architecture | 系统架构

<p align="center">
  <img src="docs/images/docsentinel-architect.png" width="200" alt="DocSentinel Architect"/>
</p>

**DocSentinel** — System Architecture Document (open-source style)

|                  |                                                                           |
| :--------------- | :------------------------------------------------------------------------ |
| **Version**      | 4.0                                                                       |
| **Author**       | PAN CHAO                                                                  |
| **Last updated** | 2026-03                                                                   |
| **Related**      | [Product Requirements (PRD)](./SPEC.md) · [Design docs](./docs/README.md) |

---

## Overview | 概述

DocSentinel is an **AI-powered SSDLC (Secure Software Development Lifecycle) platform** that automates security activities across all six phases of the software development lifecycle. Built on **LangChain** and **LangGraph**, the system orchestrates phase-specific AI agents to perform security assessments of documents, questionnaires, and reports — from requirements analysis and threat modeling to vulnerability monitoring and incident response — providing stateful, graph-based agent workflows with stage-aware routing. This document describes the **system architecture**: high-level design, components, data flow, integrations, and deployment. For product goals and requirements, see [SPEC.md](./SPEC.md).

---

## Goals & Context | 目标与背景

-   **Goal**: Provide AI-assisted security coverage across the entire SSDLC — Requirements, Design, Development, Testing, Deployment, and Operations — reducing manual effort for security teams while improving coverage and consistency. Automate first-pass assessment of security-related documents (questionnaires, design docs, compliance evidence) and produce structured reports (risks, compliance gaps, remediations).
-   **Context**: Enterprise security teams must embed security into every phase of delivery (Shift-Left), aligned with frameworks like NIST SSDF, OWASP SAMM, Microsoft SDL, and SOC2. The system provides phase-specific agents orchestrated by LangGraph, a unified knowledge base (RAG) with phase-specific collections, multi-format parsing, pluggable LLMs (cloud or local) via LangChain, and **SSDLC-aware assessment pipelines**.

---

## High-Level Architecture | 高层架构

The system is organized in layers: **Access** → **SSDLC Orchestration (LangGraph)** → **Core Services (KB, Parser, Memory, Skills)** → **LLM Abstraction (LangChain)** → **LLM Backends**. External integrations (AAD, ServiceNow, SAST/DAST tools) connect at the access and orchestration boundaries.

![DocSentinel Architecture Overview](docsentinel_architecture.png)

### Mermaid: Logical View

```mermaid
flowchart TB
    subgraph Users["Users"]
        Staff["Security Staff"]
        APIUser["API / CI-CD / MCP"]
    end
    subgraph Access["Access Layer"]
        API["REST API\n(FastAPI)"]
        MCP["MCP Server\n(stdio)"]
    end
    subgraph Orchestration["SSDLC Orchestration (LangGraph)"]
        Router["Phase Router"]
        subgraph Agents["Phase Agents"]
            A1["Requirements\nAgent"]
            A2["Design\nAgent"]
            A3["Development\nAgent"]
            A4["Testing\nAgent"]
            A5["Deployment\nAgent"]
            A6["Operations\nAgent"]
        end
        State["Shared State\n& Checkpointing"]
    end
    subgraph Core["Core Services"]
        KB["Knowledge Base\n(RAG)"]
        Parser["Parser"]
        Mem["Memory"]
        Skill["Skills"]
    end
    subgraph LLM["LLM Layer (LangChain)"]
        Abst["LLM Abstraction"]
    end
    subgraph Backends["LLM Backends"]
        Cloud["OpenAI / Claude / Qwen"]
        Local["Ollama / vLLM"]
    end
    subgraph Integrations["Integrations"]
        AAD["AAD (SSO)"]
        SN["ServiceNow"]
        Tools["SAST / DAST\nTools"]
    end

    Staff --> API
    APIUser --> API
    APIUser --> MCP
    API --> Router
    MCP --> Router
    Router --> A1
    Router --> A2
    Router --> A3
    Router --> A4
    Router --> A5
    Router --> A6
    A1 & A2 & A3 & A4 & A5 & A6 <--> State
    A1 & A2 & A3 & A4 & A5 & A6 --> KB
    A1 & A2 & A3 & A4 & A5 & A6 --> Parser
    A1 & A2 & A3 & A4 & A5 & A6 --> Skill
    A1 & A2 & A3 & A4 & A5 & A6 --> Abst
    Abst --> Cloud
    Abst --> Local
    Router -.-> AAD
    Router -.-> SN
    A4 -.-> Tools
```

---

## SSDLC Agent Design | SSDLC Agent 设计

### LangGraph State Machine | LangGraph 状态机

The core orchestration is a **LangGraph StateGraph** where each SSDLC phase is a node. Edges define the workflow — sequential, parallel, or conditional based on project context and user configuration.

```mermaid
stateDiagram-v2
    [*] --> Router
    Router --> Requirements: phase=requirements
    Router --> Design: phase=design
    Router --> Development: phase=development
    Router --> Testing: phase=testing
    Router --> Deployment: phase=deployment
    Router --> Operations: phase=operations
    Router --> FullSSDLC: phase=full

    state FullSSDLC {
        [*] --> Requirements
        Requirements --> Design
        Design --> Development
        Development --> Testing
        Testing --> Deployment
        Deployment --> Operations
        Operations --> [*]
    }

    Requirements --> Reviewer
    Design --> Reviewer
    Development --> Reviewer
    Testing --> Reviewer
    Deployment --> Reviewer
    Operations --> Reviewer
    Reviewer --> [*]
```

**Key Design Decisions:**

-   **Shared State**: All agents read/write to a shared `SSDLCState` TypedDict managed by LangGraph. This enables cross-phase traceability (e.g. threat from Design is linked to test case in Testing).
-   **Checkpointing**: LangGraph's built-in checkpointing persists state across requests, enabling long-running multi-phase assessments.
-   **Conditional Routing**: The Router node inspects the request (phase, project type, risk level) and routes to the appropriate agent(s). For full SSDLC, agents execute in sequence with optional parallel sub-steps.
-   **Human-in-the-Loop**: LangGraph interrupt points allow human review before progressing to the next phase.

### Phase Agent Details | 阶段 Agent 详情

| Agent | SSDLC Phase | Key Tools / Skills | Input Examples | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Requirements Agent** | Requirements | Compliance matcher, risk classifier, requirements extractor | PRDs, BRDs, user stories | Security requirements list, compliance obligations, risk classification |
| **Design Agent** | Design | STRIDE analyzer, architecture reviewer, SDR generator | Architecture docs, design specs, data flow diagrams | Threat model (STRIDE/DREAD), SDR report, security architecture findings |
| **Development Agent** | Development | Secure coding checker, SAST triage, code reviewer | Source code, coding guidelines, SAST reports | Secure coding findings, SAST triage results, coding recommendations |
| **Testing Agent** | Testing | SAST/DAST parser, pentest analyzer, remediation tracker | SAST/DAST reports, pentest findings | Prioritized vulnerabilities, remediation plan, fix verification |
| **Deployment Agent** | Deployment | Config reviewer, hardening checker, sign-off generator | Deployment configs, infra-as-code, release checklists | Configuration findings, hardening gaps, release sign-off report |
| **Operations Agent** | Operations | CVE analyzer, incident assistant, log auditor | CVE feeds, incident reports, security logs | Vulnerability alerts, incident analysis, audit findings |

---

## Component Design | 组件设计

### 1. Access Layer | 接入层

-   **REST API** (FastAPI): Request validation, routing to SSDLC assessment / KB / health / skills endpoints. Phase-aware endpoints (e.g. `POST /assessments/{phase}`).
-   **MCP Server** (Model Context Protocol): Standard stdio interface for autonomous agents (Claude Desktop, Cursor, OpenClaw) to discover and call SSDLC tools.
-   **Note**: v4.0 is a **headless API + MCP service**. Authentication (AAD/JWT) and rate limiting are defined but not yet wired into endpoints.

### 2. SSDLC Orchestrator (LangGraph) | SSDLC 编排器

-   Built on **LangChain + LangGraph**: stateful, graph-based agent workflow with conditional edges.
-   **Graph Definition**: `StateGraph` with nodes for Router, 6 phase agents, and Reviewer. Graph nodes: Parser → SSDLC Router → Policy+History Agent ∥ Evidence Agent → Drafter Agent → Reviewer Agent.
-   **State Schema**: `SSDLCState` TypedDict containing parsed documents, phase findings, threat models, cross-phase references, and metadata.
-   **Conditional Edges**: Route based on requested phase, project risk level, or full SSDLC mode. SSDLC Router node determines the lifecycle stage and injects stage-specific skill + checklist.
-   **Parallel Execution**: Policy and Evidence nodes run **in parallel** (LangGraph fan-out/fan-in). Within phases, sub-tasks (e.g. KB lookup + document parsing) run concurrently via `asyncio.gather`.
-   **Checkpointing**: Persistent state via LangGraph `MemorySaver` or database-backed checkpointer.
-   Assessment submission is **non-blocking** — returns task_id immediately, processes in background.
-   Singleton `KnowledgeBaseService` and cached LLM client shared across requests.

### 3. Memory | 记忆体

-   **Working memory**: LangGraph shared state (`SSDLCState`) persisted via checkpointing.
-   **Cross-phase context**: Findings from earlier phases are carried forward automatically (e.g. Design threats → Testing test cases).
-   **History reuse**: Past assessment reports are indexed into a dedicated Chroma collection and retrieved as context for new assessments.
-   **Status**: LangGraph `MemorySaver` for MVP; database-backed checkpointer for production.

### 4. Skills & Personas | 技能与角色

-   **Persona-based Assessment**: Defines "who" is assessing (e.g. ISO 27001 Auditor vs. AppSec Engineer).
-   **Built-in Persona Skills**: 4 hardcoded personas (ISO 27001 Auditor, AppSec Engineer, GDPR DPO, Cloud Architect) in `skills_registry.py`.
-   **Phase-specific Personas**: Each SSDLC phase has dedicated personas:
    -   Requirements: Compliance Analyst, Risk Assessor
    -   Design: Threat Modeler, Security Architect
    -   Development: Secure Code Reviewer, SAST Analyst
    -   Testing: Pentest Analyst, Vulnerability Manager
    -   Deployment: Release Security Reviewer, Hardening Specialist
    -   Operations: Vulnerability Monitor, Incident Responder
-   **Built-in SSDLC Skills**: 6 stage-specific skills (one per SSDLC stage) with tailored `system_prompt`, `risk_focus`, checklists, and `compliance_frameworks`.
-   **Custom Skills**: File-backed (`data/skills.json`) CRUD via REST API.
-   **Dynamic Orchestration**: LangGraph injects skill-specific context into RAG queries and LLM prompts based on the selected persona and SSDLC stage.

### 5. Knowledge Base (RAG) | 知识库

-   **Vector Store**: ChromaDB for chunk-level similarity search (sentence-transformers embeddings).
-   **Graph RAG**: LightRAG for entity-relationship aware retrieval (controls → policies → vulnerabilities → threats). Enabled via `ENABLE_GRAPH_RAG` config.
-   **Phase-specific Collections**: Separate knowledge collections per SSDLC phase:
    -   `kb_requirements`: Compliance frameworks, security policies, requirement templates
    -   `kb_design`: Security patterns, threat catalogs, architecture guidelines
    -   `kb_development`: Secure coding standards, OWASP guidelines, language-specific practices
    -   `kb_testing`: Vulnerability databases, testing methodologies, remediation guides
    -   `kb_deployment`: CIS benchmarks, hardening guides, configuration standards
    -   `kb_operations`: CVE databases, incident playbooks, audit checklists
-   **Hybrid Query**: When Graph RAG is enabled, results from both vector and graph retrieval are merged and deduplicated.
-   **History Reuse**: Indexes past assessment responses into a dedicated Chroma collection.
-   **Singleton**: Single `KnowledgeBaseService` instance shared across the application lifecycle.

### 6. Parser | 文件解析

-   **Primary engine**: Docling — preserves tables, headings, and supports OCR for scanned PDFs. Outputs structured Markdown.
-   **Fallback engine**: Legacy parsers (PyMuPDF, python-docx, openpyxl, python-pptx) for when Docling is unavailable.
-   **SAST/DAST Report Parsers**: Dedicated parsers for SARIF format, SonarQube JSON, Checkmarx XML, Burp Suite XML, OWASP ZAP reports.
-   **Engine selection**: Configurable via `PARSER_ENGINE` (`auto` / `docling` / `legacy`). `auto` tries Docling first, falls back to legacy.
-   Shared pipeline for both assessment input and KB document ingestion.

### 7. LLM Abstraction (LangChain) | LLM 抽象层

-   Single interface for chat/completion via **LangChain** (`ChatOpenAI` / `ChatOllama`).
-   LangChain is also the foundation for LangGraph agent nodes — each node uses LangChain's `Runnable` interface.
-   **LangChain Tools**: Phase agents use LangChain tools for structured interactions (KB query, document parsing, report generation).
-   **Prompt Management**: LangChain `ChatPromptTemplate` with phase-specific system prompts and few-shot examples.
-   **Cached client**: LLM instance is `@lru_cache`d — one client per process lifetime.
-   Supported providers: OpenAI (and compatible APIs), **Ollama** (local).

```mermaid
flowchart LR
    subgraph Agents["Phase Agents"]
        A["Requirements / Design / Dev / Test / Deploy / Ops"]
    end
    subgraph LangChain["LangChain"]
        Tools["Tools"]
        Prompts["Prompt Templates"]
        LLM["LLM Abstraction"]
    end
    subgraph Providers["Providers"]
        O["OpenAI"]
        Ol["Ollama"]
    end
    A --> Tools
    A --> Prompts
    Tools --> LLM
    Prompts --> LLM
    LLM --> O
    LLM --> Ol
```

---

## SSDLC Pipeline | SSDLC 流水线

DocSentinel supports all 6 SSDLC stages defined by NIST, OWASP, and Microsoft SDL. Each stage has a dedicated skill with stage-specific prompts, checklists, and risk focus areas.

```mermaid
flowchart LR
    subgraph SSDLC["SSDLC Stages"]
        S1["1. Requirements\n需求"]
        S2["2. Design\n设计"]
        S3["3. Development\n开发"]
        S4["4. Testing\n测试"]
        S5["5. Deployment\n部署"]
        S6["6. Operations\n运维"]
    end
    S1 --> S2 --> S3 --> S4 --> S5 --> S6
```

| Stage | Key Assessment Focus | Example Inputs |
| :---- | :------------------- | :------------- |
| **Requirements** | Security requirements completeness, compliance mapping (GDPR, ISO 27001), risk analysis | Requirements docs, compliance checklists |
| **Design** | Security architecture, STRIDE/DREAD threat model, encryption/permission design, SDR | Architecture docs, threat models, data flow diagrams |
| **Development** | Secure coding standards, built-in controls (anti-injection, XSS), code review findings | Code review reports, coding guidelines |
| **Testing** | SAST/DAST triage, penetration test evaluation, vulnerability fix verification | Scan reports, pen-test findings |
| **Deployment** | Release readiness, config security, key management, least privilege, hardening | Deployment configs, release checklists |
| **Operations** | Vulnerability monitoring, incident response, patch management, log audit | Incident reports, audit logs, monitoring alerts |

### LangGraph Agent Flow

```mermaid
stateDiagram-v2
    [*] --> Parse: files received
    Parse --> SSDLCRouter: parsed docs
    SSDLCRouter --> PolicyAgent: stage + skill loaded
    SSDLCRouter --> EvidenceAgent: stage + skill loaded
    state fork_state <<fork>>
    PolicyAgent --> fork_state
    EvidenceAgent --> fork_state
    fork_state --> DrafterAgent: policy_chunks + evidence
    DrafterAgent --> ReviewerAgent: draft report
    ReviewerAgent --> [*]: final report + confidence
```

The **SSDLC Router** is a LangGraph node that:
1. Accepts an explicit `ssdlc_stage` parameter, or auto-detects the stage from document content.
2. Loads the corresponding stage skill (system prompt, risk focus, checklist).
3. Routes to the parallel Policy+Evidence fan-out, then sequentially to Drafter and Reviewer.

---

## Data Flow | 数据流

End-to-end flow for an SSDLC assessment:

```mermaid
sequenceDiagram
    participant U as User
    participant API as REST API
    participant LG as LangGraph Router
    participant Agent as Phase Agent
    participant Parser as Parser
    participant Router as SSDLC Router
    participant KB as Knowledge Base
    participant Skill as Skill
    participant LLM as LLM (LangChain)
    participant Review as Human Review

    U->>API: POST /assessments (files, phase, scenario_id, ssdlc_stage?)
    API-->>U: 202 Accepted (task_id)
    API->>LG: background task: route(phase, files, context)
    LG->>Parser: parse(files)
    Parser-->>LG: parsed docs
    LG->>Agent: execute(parsed_docs, state)
    Agent->>KB: query(phase_collection, relevant policy)
    KB-->>Agent: chunks
    Agent->>Skill: apply(persona, parsed_docs, chunks)
    Skill->>LLM: prompt + context
    LLM-->>Skill: structured findings
    Skill-->>Agent: phase findings
    Agent-->>LG: update state (findings, threats, gaps)
    LG->>LG: checkpoint state
    LG-->>API: assessment report
    U->>API: GET /assessments/{task_id}
    API-->>U: report
    U->>Review: review & approve/reject
```

**Full SSDLC Flow:**

1.  User submits files and selects phase(s) or "full SSDLC" mode (and optional `ssdlc_stage` / skill ID). API returns `task_id` immediately (non-blocking).
2.  **Parser** converts files to unified Markdown/text format (Docling or legacy).
3.  **LangGraph Router** determines which phase agent(s) to invoke and loads stage-specific skill + checklist.
4.  For full SSDLC, agents execute sequentially (Requirements → Design → Development → Testing → Deployment → Operations), with findings from each phase carried forward in shared state. **Policy+History Agent** queries KB (vector + graph RAG) and **Evidence Agent** scans documents — these run **in parallel** via LangGraph fan-out.
5.  Each **Phase Agent**: parses documents → queries phase-specific KB → applies skill persona → calls LLM → produces structured findings.
6.  **Drafter Agent** synthesizes findings into a structured report via LLM, guided by the stage checklist.
7.  **Reviewer** node validates completeness, assigns confidence (0.0-1.0), cross-references findings across phases.
8.  Report with cross-phase traceability is returned for **human-in-the-loop** review. User polls `GET /assessments/{task_id}` to retrieve the completed report.

---

## Integration Points | 集成

```mermaid
flowchart LR
    subgraph DocSentinel["DocSentinel"]
        API["API"]
        LG["LangGraph\nOrchestrator"]
        Agents["Phase Agents"]
    end
    subgraph IdP["Identity"]
        AAD["Azure AD / Entra ID"]
    end
    subgraph PM["Project Management"]
        SN["ServiceNow"]
    end
    subgraph SecTools["Security Tools"]
        SAST["SAST\n(SonarQube, Checkmarx)"]
        DAST["DAST\n(Burp, ZAP)"]
        Scanner["Vuln Scanners\n(Nessus, Qualys)"]
    end
    User["User"] -->|Login / Token| AAD
    AAD -->|JWT / SSO| API
    LG -->|Project metadata| SN
    Agents -->|Parse reports| SAST
    Agents -->|Parse reports| DAST
    Agents -->|CVE feeds| Scanner
```

-   **AAD**: SSO and API token validation (OAuth2/OIDC).
-   **ServiceNow**: Read project metadata (type, compliance scope, owner); optional write-back of assessment results.
-   **SAST/DAST Tools**: Import scan results in SARIF, native JSON/XML formats for automated triage by Testing Agent.
-   **Vulnerability Scanners**: CVE feed integration for Operations Agent monitoring.

See [docs/04-integration-guide.md](./docs/04-integration-guide.md) for configuration and field mapping.

---

## Security Architecture | 安全架构

Security is designed along five areas (detailed in [PRD §7.2](./SPEC.md)):

| Area | Summary |
| :--- | :--- |
| **Identity & access** | AAD/SSO, RBAC (analyst, lead, project owner, API consumer, admin), token/API key, data isolation by project/role. |
| **Data** | TLS for transport; secrets not in code; minimal retention; optional local-only LLM for data sovereignty. |
| **Application** | Input validation, injection prevention (including prompt injection), dependency/SCA, safe error responses, security headers, rate limiting. |
| **Operations** | Audit log (who/what/when), LangGraph state transition logging, alerting, backup and recovery. |
| **Supply chain** | Trusted dependencies, vulnerability handling, license compliance. |

---

## Deployment View | 部署视图

```mermaid
flowchart TB
    subgraph Client["Client"]
        Browser["Browser / CLI / CI-CD / MCP Agent"]
    end
    subgraph Server["Server / Container"]
        App["DocSentinel\n(FastAPI + LangGraph)"]
        Chroma["Chroma\n(vector store)"]
        Checkpoint["LangGraph\nCheckpoint Store"]
    end
    subgraph External["External"]
        AAD["AAD"]
        SN["ServiceNow"]
        LLM["LLM (OpenAI / Ollama)"]
        SecTools["SAST/DAST Tools"]
    end
    Browser --> App
    App --> Chroma
    App --> Checkpoint
    App --> AAD
    App --> SN
    App --> LLM
    App --> SecTools
```

-   **Runtime**: Python 3.10+, FastAPI, Uvicorn, LangGraph, LangChain.
-   **Storage**: Vector store (Chroma) persisted on disk; LangGraph checkpoint store (memory/SQLite/PostgreSQL); optional Redis for sessions.
-   **Network**: Outbound to AAD, ServiceNow, LLM endpoints, and SAST/DAST tools; TLS recommended for production.
-   **Deployment**: Single node / container for MVP; scale out by separating API and agent workers if needed.

See [docs/05-deployment-runbook.md](./docs/05-deployment-runbook.md) for environment, configuration, and runbook.

---

## References | 参考

| Document | Description |
| :--- | :--- |
| [SPEC.md](./SPEC.md) | Product requirements, SSDLC phases, features, security controls. |
| [docs/01-architecture-and-tech-stack.md](./docs/01-architecture-and-tech-stack.md) | Technology choices and module layout. |
| [docs/02-api-specification.yaml](./docs/02-api-specification.yaml) | OpenAPI spec. |
| [docs/03-assessment-report-and-skill-contract.md](./docs/03-assessment-report-and-skill-contract.md) | Report schema and Skill I/O. |
| [docs/04-integration-guide.md](./docs/04-integration-guide.md) | AAD, ServiceNow, SAST/DAST integration. |
| [docs/05-deployment-runbook.md](./docs/05-deployment-runbook.md) | Deployment and operations. |

---

*This architecture document is part of the [DocSentinel](https://github.com/arthurpanhku/DocSentinel) open-source project.*
