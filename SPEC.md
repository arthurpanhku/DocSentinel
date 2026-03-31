# DocSentinel — Product Requirements Document (PRD) | 产品需求文档

|             |                         |
| :---------- | :---------------------- |
| **Version** | v3.0                    |
| **Date**    | 2026-03-30              |
| **Author**  | PAN CHAO                |
| **Contact** | u3638376@connect.hku.hk |

> **System Architecture | 系统架构文档**
>
> Full system architecture (diagrams, data flow, deployment) is maintained in:
> 完整的系统架构说明（含图示、数据流、部署视图）已单独成文：
>
> **[ARCHITECTURE.md](./ARCHITECTURE.md)**
>
> *Section 5 of this PRD contains only an architecture summary and index.*
> *本文 PRD 第五节仅保留架构摘要与索引。*

**History | 版本历史**

-   **v3.0**: Major upgrade. Pivoted to **SSDLC (Secure Software Development Lifecycle)** full-phase support; introduced **LangChain + LangGraph** as Agent orchestration framework; redesigned multi-agent pipeline with phase-specific SSDLC agents.
    重大更新。转向 **SSDLC（安全开发生命周期）** 全阶段支持；引入 **LangChain + LangGraph** 作为 Agent 编排框架；重新设计基于 SSDLC 阶段的多代理流水线。
-   **v2.0**: Major upgrade. Added Multi-Agent Orchestration, Human-in-the-Loop Workflow, Skill/Persona Management, and One-Click Deployment.
    重大更新。新增多代理编排、人机协作流、技能/角色管理及一键部署。
-   **v1.4**: PRD and System Architecture doc split.
    PRD 与系统架构文档分离。
-   **v1.3**: Added "Security Requirements and Controls".
    新增非业务性「安全需求与安全控制」。
-   **v1.2**: KB multi-format upload & open-source parsing; Parser reuse.
    知识库多格式上传与开源解析、Parser 复用。
-   **v1.1**: Enterprise integration (ServiceNow), IAM (AAD/SSO, RBAC), Deployment.
    企业集成（ServiceNow）、IAM（AAD/SSO、RBAC）、部署与连通性。

---

## 1. Document Purpose | 文档说明

**English**

This PRD is for the open-source "DocSentinel" project. It defines business pain points, solution approach, system architecture, and product scope to serve as a single source of truth for subsequent design and development. The project aims to build an **AI-powered SSDLC (Secure Software Development Lifecycle) platform** that automates security activities across all six phases of the software development lifecycle — from requirements gathering to production operations. Powered by **LangChain and LangGraph** for intelligent agent orchestration, it helps enterprise security teams embed security into every stage of delivery, not just the final review.

**中文**

本 PRD 面向「DocSentinel」开源项目，用于明确业务痛点、解决方案、系统架构与产品范围，为后续设计与开发提供统一依据。项目目标是构建一个 **AI 驱动的 SSDLC（安全开发生命周期）平台**，自动化覆盖软件开发生命周期全部六个阶段的安全活动——从需求收集到生产运维。通过 **LangChain 与 LangGraph** 实现智能 Agent 编排，帮助企业安全团队将安全内嵌到交付的每一个环节，而非仅在最终审阅时介入。

---

## 2. Business Context and Pain Points | 业务背景与痛点

### 2.1 Business Context | 业务背景

**English**

Enterprise Cyber Security teams operate under multiple constraints:

-   **Diverse reference sources**: Internal security policies, industry best practices (e.g. NIST SSDF, OWASP, CISA), past project cases, and compliance frameworks (e.g. SOC2, ISO 27001, PCI DSS).
-   **Full SSDLC coverage**: Security review and control requirements exist at every stage — requirements/design, development, testing, deployment, and operations — but most tools only address one or two stages.
-   **Wide variety of deliverables**: Security questionnaires, threat models, architecture documents, secure coding guidelines, SAST/DAST reports, penetration test findings, deployment checklists, compliance evidence, and audit materials all require manual reading, comparison, and sign-off.
-   **Shift-left pressure**: Modern DevSecOps demands security involvement early in the lifecycle, but security teams lack tooling to scale across requirements, design, and development phases.

In agile and DevOps environments, enterprises ship dozens to hundreds of projects per year. Security teams must complete large volumes of assessments and reviews with limited headcount, creating a clear bottleneck — especially when coverage is expected across the entire SSDLC, not just pre-release reviews.

**中文**

大型企业的 Cyber Security 团队需要在以下多维度约束下工作：

-   **依据来源多样**：公司内部 Security Policy、行业最佳实践（如 NIST SSDF、OWASP、CISA 等）、历史项目案例与合规框架（如 SOC2、ISO 27001、PCI DSS）。
-   **流程覆盖完整 SSDLC**：从需求/设计、开发、测试、部署到运维，每个阶段都有安全评审与管控要求——但大多数工具只覆盖一两个阶段。
-   **交付物类型繁多**：安全问卷、威胁建模、架构文档、安全编码规范、SAST/DAST 报告、渗透测试结果、部署检查清单、合规证明、审计材料等，需人工阅读、比对与签字（Sign-off）。
-   **左移压力**：现代 DevSecOps 要求安全尽早介入生命周期，但安全团队缺乏在需求、设计、开发阶段规模化覆盖的工具支持。

在敏捷与 DevOps 环境下，企业每年上线项目数量从几十到几百不等，安全人员需要在有限人力下完成大量评估与审阅，成为明显瓶颈——尤其当覆盖范围从上线前审阅扩展到整个 SSDLC 时。

### 2.2 Core Pain Points | 核心痛点

| Pain Point (English) | 痛点描述 (中文) |
| :--- | :--- |
| **Fragmented SSDLC coverage**<br>Most tools cover only testing/deployment; requirements, design, and development phases lack automated security support. | **SSDLC 覆盖碎片化**<br>大多数工具仅覆盖测试/部署阶段；需求、设计和开发阶段缺乏自动化安全支持。 |
| **Fragmented assessment criteria**<br>Teams must align with policies, industry standards, and project precedents; manual lookup and alignment cost is high. | **评估依据分散**<br>需同时参照 Policy、行业标准、项目案例；人工查找与对齐成本高。 |
| **No unified threat modeling**<br>Threat models are created ad-hoc in design phase; no automated STRIDE/DREAD analysis or carry-forward to testing. | **威胁建模无统一支持**<br>设计阶段威胁模型临时创建；无自动化 STRIDE/DREAD 分析，也无法延续至测试阶段。 |
| **Heavy questionnaire workflow**<br>Multiple rounds of questionnaire filling, assessment, evidence collection, and review; inconsistent templates. | **问卷与证据流程繁重**<br>问卷—评估—证据—审阅多轮往返；模板不统一、证据质量参差。 |
| **Development-phase control relies on people**<br>Secure coding guidance, SAST result interpretation, and exception approval still depend on security staff. | **开发阶段管控依赖人工**<br>安全编码指导、SAST 结果解读、例外审批仍依赖安全人员，难以规模化。 |
| **Pre-release review pressure**<br>Security must review every file and sign off; DAST/pentest reports need interpretation. | **上线前集中审阅压力大**<br>需 Review 全部文件并 Sign-off；DAST/渗透测试报告需解读。 |
| **Post-deployment blind spots**<br>Vulnerability monitoring, incident response, and patch tracking are disconnected from the development lifecycle. | **上线后盲区**<br>漏洞监控、应急响应和补丁跟踪与开发生命周期脱节。 |
| **Scale vs. consistency**<br>Manual assessment tends to be inconsistent, incomplete, or delayed; reusable patterns are hard to institutionalize. | **规模与一致性矛盾**<br>人工评估易出现不一致、遗漏或延迟，且难以沉淀可复用的评估模式。 |

### 2.3 Desired Change | 期望改变

-   **Full lifecycle coverage / 全生命周期覆盖**: Provide AI-assisted security support across all six SSDLC phases, not just testing and deployment.
-   **Automation / 自动化**: Automate analysis and initial assessment of security artifacts at each phase — from requirements to operations.
-   **Consistency / 一致性**: Produce consistent assessment conclusions and remediation recommendations based on a unified knowledge base and policies.
-   **Intelligence / 智能化**: Use LangGraph-orchestrated agents to reason about cross-phase dependencies (e.g. a threat identified in design must be tested and monitored).
-   **Extensibility / 可扩展**: Support custom SSDLC workflows, assessment scenarios, and phase-specific skills.

---

## 3. Solution Overview | 解决方案概述

### 3.1 Product Positioning | 产品定位

**English**

Build an **AI-powered SSDLC platform for security teams**, with the primary focus on **automating security activities across the entire secure software development lifecycle**. The platform covers six standard SSDLC phases with dedicated AI agents for each:

1.  **Requirements Phase Agent**: Analyze requirements documents to identify security requirements, compliance obligations (GDPR, PCI DSS, etc.), and perform initial risk analysis.
2.  **Design Phase Agent**: Review architecture/design documents, perform automated threat modeling (STRIDE/DREAD), evaluate security architecture, encryption schemes, and access control designs. Conduct Security Design Review (SDR).
3.  **Development Phase Agent**: Assess code against secure coding standards, review SAST findings, evaluate security controls (anti-injection, XSS prevention), and provide secure coding guidance.
4.  **Testing Phase Agent**: Analyze SAST/DAST scan reports, interpret penetration test results, prioritize vulnerability fixes, and verify remediation completeness.
5.  **Deployment Phase Agent**: Review deployment configurations, evaluate secret management, assess hardening measures, and perform pre-release security sign-off checks.
6.  **Operations Phase Agent**: Monitor vulnerability feeds, assist incident response, track patch management, and audit security logs.

The platform uses **LangGraph** to orchestrate these agents into configurable workflows — agents can run sequentially, in parallel, or conditionally based on project context. **LangChain** provides the unified LLM abstraction, tool integration, and RAG pipeline.

**中文**

构建一个**面向安全团队的 AI 驱动 SSDLC 平台**，首要方向为：**自动化覆盖安全软件开发生命周期的全部安全活动**。平台为六个标准 SSDLC 阶段配备专用 AI Agent：

1.  **需求阶段 Agent**：分析需求文档，识别安全需求、合规义务（GDPR、PCI DSS 等），执行初步风险分析。
2.  **设计阶段 Agent**：审阅架构/设计文档，执行自动化威胁建模（STRIDE/DREAD），评估安全架构、加密方案、权限设计。执行安全设计评审（SDR）。
3.  **开发阶段 Agent**：对照安全编码规范评估代码，审阅 SAST 发现，评估安全控件（防注入、XSS 防护），提供安全编码指导。
4.  **测试阶段 Agent**：分析 SAST/DAST 扫描报告，解读渗透测试结果，确定漏洞修复优先级，验证整改完整性。
5.  **部署阶段 Agent**：审阅部署配置，评估密钥管理，评估加固措施，执行上线前安全检查。
6.  **运维阶段 Agent**：监控漏洞情报，辅助应急响应，跟踪补丁管理，审计安全日志。

平台使用 **LangGraph** 将这些 Agent 编排为可配置的工作流——Agent 可根据项目上下文顺序执行、并行执行或条件执行。**LangChain** 提供统一的 LLM 抽象、工具集成和 RAG 管道。

### 3.2 SSDLC Phase Details | SSDLC 阶段详述

#### Phase 1: Requirements | 需求阶段

| Activity (English) | 活动 (中文) | Agent Capability |
| :--- | :--- | :--- |
| Define security requirements | 定义安全需求 | Extract security-relevant requirements from PRDs, user stories, BRDs |
| Identify compliance obligations | 识别合规要求 | Match requirements against GDPR, PCI DSS, SOC2, ISO 27001, etc. |
| Initial risk analysis | 初步风险分析 | Classify project risk level based on data sensitivity, exposure, and scope |
| Security requirements checklist | 安全需求清单 | Generate a checklist of security requirements that must be addressed |

#### Phase 2: Design | 设计阶段

| Activity (English) | 活动 (中文) | Agent Capability |
| :--- | :--- | :--- |
| Security architecture review | 安全架构评审 | Evaluate architecture documents for security patterns and anti-patterns |
| Threat modeling (STRIDE/DREAD) | 威胁建模 | Automated STRIDE analysis on design documents; DREAD risk scoring |
| Access control & encryption design | 权限设计与加密方案 | Review IAM design, data flow encryption, key management proposals |
| Security Design Review (SDR) | 安全设计评审 | Structured SDR report with findings and recommendations |

#### Phase 3: Development | 开发阶段

| Activity (English) | 活动 (中文) | Agent Capability |
| :--- | :--- | :--- |
| Secure coding standards assessment | 安全编码规范评估 | Check code/documents against OWASP Secure Coding Practices |
| SAST findings review | SAST 结果审阅 | Triage and interpret SAST tool output, reduce false positives |
| Built-in security controls | 内置安全控件 | Evaluate anti-injection, XSS prevention, CSRF protection implementations |
| Secure coding guidance | 安全编码指导 | Provide language-specific secure coding recommendations |

#### Phase 4: Testing | 测试阶段

| Activity (English) | 活动 (中文) | Agent Capability |
| :--- | :--- | :--- |
| SAST report analysis | SAST 报告分析 | Parse and prioritize static analysis findings |
| DAST report analysis | DAST 报告分析 | Parse and interpret dynamic scan results |
| Penetration test review | 渗透测试审阅 | Analyze pentest reports, map findings to controls |
| Vulnerability fix verification | 漏洞修复验证 | Verify remediation evidence against original findings |

#### Phase 5: Deployment / Release | 部署/发布阶段

| Activity (English) | 活动 (中文) | Agent Capability |
| :--- | :--- | :--- |
| Pre-release security review | 上线前安全评审 | Checklist-based review of all phase outputs |
| Configuration security | 配置安全 | Review deployment configs, secrets management, least privilege |
| Security hardening assessment | 安全加固评估 | Evaluate server/container hardening against CIS benchmarks |
| Release sign-off | 发布签字 | Generate structured sign-off report with risk summary |

#### Phase 6: Operations / Maintenance | 运维/响应阶段

| Activity (English) | 活动 (中文) | Agent Capability |
| :--- | :--- | :--- |
| Vulnerability monitoring | 漏洞监控 | Analyze CVE feeds and vulnerability advisories against project stack |
| Incident response assistance | 应急响应辅助 | Provide structured incident analysis and response recommendations |
| Patch management tracking | 补丁管理跟踪 | Track vulnerability remediation progress and SLA compliance |
| Log audit analysis | 日志审计分析 | Analyze security logs for anomalies and compliance evidence |

### 3.3 Solution Value | 方案价值

-   **Full lifecycle / 全生命周期**: Security coverage from day one (requirements) through production operations — not just pre-release review.
-   **Cost reduction / 降本**: Reduce time security staff spend on repetitive document review across all SSDLC phases.
-   **Speed / 提速**: Shorten the cycle time at each phase; enable parallel security review with development.
-   **Intelligence / 智能化**: LangGraph-orchestrated agents maintain cross-phase context — a threat identified in design is automatically tracked through testing and deployment.
-   **Reproducibility / 可复现**: Assessment logic and criteria are captured in the knowledge base, skills, and graph-based workflows.
-   **Openness / 开放**: Support multiple commercial and local LLMs to meet requirements for data residency and cost control.

---

## 4. Product Goals and Success Metrics | 产品目标与成功指标

### 4.1 Product Goals | 产品目标

| Goal | Description |
| :--- | :--- |
| **SSDLC full coverage**<br>SSDLC 全阶段覆盖 | Provide AI-assisted security assessment across all 6 SSDLC phases with dedicated agents for each. |
| **Intelligent orchestration**<br>智能编排 | Use LangGraph to create configurable, stateful agent workflows that maintain context across SSDLC phases. |
| **Automated assessment**<br>自动化评估 | Support automatic parsing and risk assessment of common formats: security questionnaires, design documents, SAST/DAST reports, pentest findings, deployment configs, and compliance evidence. |
| **Configurable scenarios**<br>可配置评估场景 | Use the knowledge base and Skills to configure different assessment criteria by compliance framework, SSDLC phase, project type, or risk level. |
| **Multi-model support**<br>多模型支持 | Support mainstream commercial LLMs (e.g. ChatGPT, Qwen, Claude) and local/on-prem models (e.g. Ollama) through a unified LangChain interface. |
| **Actionable results**<br>结果可操作 | Output risk items, compliance gaps, threat models, remediation suggestions, and sign-off reports with traceability across phases. |

### 4.2 Success Metrics (Suggested) | 成功指标（建议）

-   **SSDLC Coverage**: Number of SSDLC phases with active agent support (target: 6/6).
-   **Coverage**: Number of supported document types (e.g. 8+ common formats) and knowledge base entries per phase.
-   **Efficiency**: Average time from upload to report generation per phase; time saved vs. manual review.
-   **Cross-phase traceability**: Percentage of findings that are tracked from identification to remediation across phases.
-   **Usability**: Steps and time to complete one "upload → assess → review → sign-off" loop per phase.
-   **Extensibility**: Configuration/development cost to add a new SSDLC phase workflow or assessment scenario.

---

## 5. System Architecture | 系统架构

> **Full Architecture Document**
>
> For detailed diagrams, data flow, deployment, and security architecture, see:
> 详细组件说明、Mermaid 架构图、数据流与时序图、集成视图、安全架构及部署视图见：
>
> **[ARCHITECTURE.md](./ARCHITECTURE.md)**

### 5.1 Architecture Summary | 架构摘要

**English**

The system uses a layered design: **Access** (REST API / MCP / CLI) → **SSDLC Orchestration** (LangGraph state machine with phase-specific agents) → **Core Services** (Knowledge Base RAG, Parser, Memory, Skills) → **LLM Abstraction** (LangChain) → **Cloud/Local LLMs**. Optional integrations: **AAD** (identity/SSO), **ServiceNow** (project metadata), and **SAST/DAST tools** (scan results ingestion).

**中文**

系统采用分层设计：**接入层**（REST API / MCP / CLI）→ **SSDLC 编排层**（LangGraph 状态机与阶段专用 Agent）→ **核心服务**（知识库 RAG、文件解析、记忆体、Skill 层）→ **LLM 抽象层**（LangChain）→ **商用/本地 LLM**。可选对接 **AAD**（身份/SSO）、**ServiceNow**（项目元数据）及 **SAST/DAST 工具**（扫描结果接入）。

**High-Level Diagram | 架构图**

```text
                    ┌─────────────────────────────────────────────────────────┐
                    │           User / Security Staff | 用户 / 安全人员         │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
                    ┌───────────────────────────▼─────────────────────────────┐
                    │            Access Layer | 接入层 (API / MCP / CLI)       │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
    ┌───────────────────────────────────────────▼───────────────────────────────────────────┐
    │                    SSDLC Orchestration (LangGraph) | SSDLC 编排层                      │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
    │  │ Require- │ │  Design  │ │  Dev     │ │  Test    │ │  Deploy  │ │  Ops     │       │
    │  │ ments    │ │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │       │
    │  │ Agent    │ │          │ │          │ │          │ │          │ │          │       │
    │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
    │       └─────────────┴────────────┴─────────────┴────────────┴────────────┘             │
    │                                    │                                                    │
    │  ┌─────────────┐  ┌─────────────┐  │  ┌─────────────┐  ┌─────────────┐                 │
    │  │   Memory    │  │   Skills    │  │  │ KB (RAG)    │  │   Parser   │                 │
    │  │   记忆体     │  │   Skill 层  │  │  │   知识库     │  │  文件解析   │                 │
    │  └─────────────┘  └─────────────┘  │  └─────────────┘  └─────────────┘                 │
    │                                    │                                                    │
    │                        ┌───────────▼───────────┐                                       │
    │                        │ LLM Abstraction Layer  │                                       │
    │                        │   (LangChain)          │                                       │
    │                        └───────────┬───────────┘                                       │
    └────────────────────────────────────┼───────────────────────────────────────────────────┘
                                         │
        ┌───────────────────────────────┼───────────────────────────────────┐
        │  Commercial/Cloud LLM         │    Local/On-prem LLM              │
        │  ChatGPT / Claude / Qwen      │    Ollama / vLLM / ...            │
        └───────────────────────────────────────────────────────────────────┘
```

### 5.2 Component Index | 核心组件索引

| Component | Role | Details |
| :--- | :--- | :--- |
| **SSDLC Orchestrator** | LangGraph state machine coordinating phase agents with conditional routing and shared state. | ARCHITECTURE.md § Component Design |
| **Phase Agents** | Six dedicated agents, each with phase-specific prompts, tools, and evaluation criteria. | ARCHITECTURE.md § SSDLC Agents |
| **Memory** | Manages working, episodic, and cross-phase state via LangGraph checkpointing. | ARCHITECTURE.md § Component Design |
| **Skills** | Reusable assessment capabilities (e.g. threat modeling, SAST triage, compliance check). | ARCHITECTURE.md § Component Design |
| **Knowledge Base** | Multi-format ingestion, chunking, embedding, hybrid RAG (vector + graph). | ARCHITECTURE.md § Component Design |
| **Parser** | Converts files (PDF, Word, Excel, SAST/DAST reports, etc.) to Markdown/JSON. | ARCHITECTURE.md § Component Design |
| **LLM Abstraction** | LangChain unified interface for model switching. | ARCHITECTURE.md § Component Design |
| **Integrations** | AAD (SSO), ServiceNow (metadata), SAST/DAST tool connectors. | ARCHITECTURE.md § Integration Points |

### 5.3 Data Flow (Summary) | 数据流（简要）

1.  User submits **SSDLC assessment task** (files + phase + optional project/scenario) via API/MCP.
2.  (Optional) Fetch **project metadata** from ServiceNow.
3.  **Parser** converts files to intermediate format.
4.  **LangGraph Orchestrator** routes to the appropriate **Phase Agent(s)**.
5.  Phase Agent(s) load **Knowledge Base** chunks (RAG) and **Skills**, call **LLM** with context.
6.  Generate structured **assessment report** (risks, gaps, threat model, remediations) with cross-phase traceability.
7.  Results stored for **human-in-the-loop** review and sign-off.

---

## 6. Scope and User Stories | 功能范围与用户故事

### 6.1 Core Feature List | 核心功能列表

| Module | Feature | Priority |
| :--- | :--- | :--- |
| **SSDLC Orchestrator** | LangGraph-based state machine with 6 phase agents and conditional routing. | P0 |
| **SSDLC Orchestrator** | Cross-phase state management and finding traceability. | P0 |
| **SSDLC Orchestrator** | Configurable workflows: sequential, parallel, or selective phase execution. | P1 |
| **Requirements Agent** | Analyze requirements docs for security requirements and compliance obligations. | P0 |
| **Design Agent** | Automated threat modeling (STRIDE/DREAD) from architecture documents. | P0 |
| **Design Agent** | Security Design Review (SDR) report generation. | P0 |
| **Development Agent** | Secure coding assessment against OWASP standards. | P0 |
| **Development Agent** | SAST findings triage and interpretation. | P1 |
| **Testing Agent** | SAST/DAST report parsing and vulnerability prioritization. | P0 |
| **Testing Agent** | Penetration test report analysis and remediation tracking. | P1 |
| **Deployment Agent** | Pre-release security checklist and configuration review. | P0 |
| **Deployment Agent** | CIS benchmark assessment for hardening. | P1 |
| **Operations Agent** | Vulnerability monitoring and CVE analysis against project stack. | P1 |
| **Operations Agent** | Incident response assistance and log audit. | P2 |
| **Parser** | Upload Word / PDF / Excel / PPT / SAST/DAST reports and convert to JSON/Markdown. | P0 |
| **Parser** | OCR / Vision support for images. | P1 |
| **Knowledge Base** | Upload multi-format docs, parse, chunk, embed, and retrieve (RAG). | P0 |
| **Knowledge Base** | Metadata filtering (e.g. by framework, SSDLC phase, project). | P1 |
| **Knowledge Base** | Phase-specific knowledge collections (requirements policies, design patterns, coding standards, etc.). | P0 |
| **Assessment** | Select SSDLC phase and scenario, upload files, trigger assessment. | P0 |
| **Assessment** | Output structured report (Risks, Gaps, Threat Model, Remediation, Confidence). | P0 |
| **Assessment** | **Human-in-the-Loop**: Review, approve, reject, comment workflow. | P0 |
| **LLM** | Configurable commercial LLMs (OpenAI, Claude, etc.) via LangChain. | P0 |
| **LLM** | Configurable local models (Ollama) via LangChain. | P0 |
| **Skill** | **Skill/Persona Management**: Create custom roles and import templates. | P0 |
| **Skill** | Built-in personas per SSDLC phase (e.g. Threat Modeler, Secure Code Reviewer, Pentest Analyst). | P0 |
| **Memory** | LangGraph checkpointing for cross-phase state persistence. | P0 |
| **Memory** | **History Reuse**: Retrieve past similar assessments. | P1 |
| **Access** | REST API; MCP Server for agent integration. | P0 |
| **Integrations** | ServiceNow: Read project metadata, write back results. | P1 |
| **Integrations** | SAST/DAST tool connectors (SonarQube, Checkmarx, Burp, etc.). | P1 |
| **IAM** | AAD (Azure AD) Login & SSO. | P0 |
| **IAM** | RBAC (Analyst, Lead, Project Owner, Admin, API Consumer). | P0 |
| **IAM** | API Authentication (Bearer Token / API Key). | P0 |
| **IAM** | Data isolation by project/role. | P0 |

### 6.2 User Stories (Examples) | 用户故事（示例）

-   **As a security team member**, I want to upload a project's requirements document and have the Requirements Agent automatically identify missing security requirements and compliance obligations **so that** I can provide early feedback before design begins.
-   **As a security architect**, I want to submit an architecture document to the Design Agent and receive an automated STRIDE threat model **so that** I can focus on reviewing and validating threats rather than creating the initial model from scratch.
-   **As a security lead**, I want to run a full SSDLC assessment across multiple phases for a project **so that** I get a unified view of security posture from requirements through deployment.
-   **As a developer**, I want to submit my code review package and SAST results to the Development Agent **so that** I get prioritized findings with secure coding guidance specific to my language and framework.
-   **As a pentest manager**, I want to upload penetration test reports to the Testing Agent **so that** findings are automatically mapped to the original threat model and remediation is tracked.
-   **As an operations engineer**, I want the Operations Agent to analyze new CVE feeds against our deployment stack **so that** I know which vulnerabilities require immediate patching.
-   **As enterprise IT**, I want to configure the platform to use only a local Ollama model **so that** all assessment data stays within the internal network.
-   **As a DevSecOps engineer**, I want to integrate the assessment API into our CI/CD pipeline **so that** security checks run automatically at each stage.

---

## 7. Non-Functional Requirements | 非功能需求

### 7.1 General NFRs | 通用非功能需求

| Category | Requirement (English) | 要求 (中文) |
| :--- | :--- | :--- |
| **Security & Privacy** | Support fully local/on-prem deployment and local LLM; support audit logs. | 支持纯本地部署与本地 LLM；支持审计日志。 |
| **Performance** | Acceptable end-to-end latency for single-phase assessment; parallel phase execution for full SSDLC. | 单阶段评估时延可接受；全 SSDLC 评估支持并行执行。 |
| **Maintainability** | KB, Skills, LangGraph workflows, and LLM config maintainable via config/API without code changes. | 知识库、Skill、LangGraph 工作流、LLM 可配置，无需改代码扩展。 |
| **Observability** | Log model usage, tokens, duration, errors, and agent state transitions. | 记录模型、token、耗时、错误及 Agent 状态转换。 |
| **Auth & Isolation** | RBAC and data isolation by project/role; fine-grained auth via AAD/ServiceNow. | 按角色与项目隔离数据；细粒度授权。 |
| **Deployment** | Support on-prem/private deployment; connectivity to AAD/ServiceNow/LLM/SAST/DAST tools. | 支持内网部署；需连通 AAD/ServiceNow/LLM/SAST/DAST 工具。 |
| **Open Source** | Architecture aligns with mainstream open-source Agent projects (LangChain/LangGraph ecosystem). | 架构对齐 LangChain/LangGraph 生态，便于社区贡献。 |

### 7.2 Security Requirements and Controls (Non-Functional) | 安全需求与控制

This section defines security controls for the **system itself** (not the documents being assessed).

**7.2.1 Control Domains | 控制域**

-   **IAM**: Identity and Access Control (身份与访问控制)
-   **DATA**: Data Security (数据安全)
-   **APP**: Application Security (应用安全)
-   **OPS**: Operations and Audit (运维与审计)
-   **SCM**: Supply Chain and Open Source (供应链与开源)

**7.2.2 Identity and Access Control | 身份与访问控制**

-   **IAM-01**: All user/integration endpoints must require authentication (except health checks).
-   **IAM-02**: Strong auth: AAD/OIDC SSO; API Bearer JWT or API Key (no secrets in URL).
-   **IAM-03**: RBAC with least privilege default.
-   **IAM-04**: Session/Token timeout and revocation.
-   **IAM-05**: Sensitive operations (e.g. delete KB, modify workflows) require confirmation or higher privilege.

**7.2.3 Data Security | 数据安全**

-   **DATA-01**: TLS (1.2+) for all transport.
-   **DATA-02**: Encryption at rest for sensitive data; secrets management (no plaintext in code).
-   **DATA-03**: Data minimization and retention policy.
-   **DATA-04**: PII handling compliance (access control, audit).
-   **DATA-05**: Clarify LLM data usage (cloud vs. local) for data sovereignty.

**7.2.4 Application Security | 应用安全**

-   **APP-01**: Input validation (file type, size, path traversal).
-   **APP-02**: Injection prevention (prompt injection mitigation, SQLi/Command injection).
-   **APP-03**: Dependency scanning (SCA) and updates.
-   **APP-04**: Safe error handling (no stack traces to users).
-   **APP-05**: Web protections (CSRF, security headers, rate limiting).

**7.2.5 Operations and Audit | 运维与审计**

-   **OPS-01**: Audit logs (who, what, when, resource) protected from tampering.
-   **OPS-02**: Operational logs (performance, errors, agent state transitions) without sensitive content.
-   **OPS-03**: Security event detection and alerting.
-   **OPS-04**: Backup and recovery for critical data (KB, assessment history, LangGraph checkpoints).

**7.2.6 Supply Chain | 供应链**

-   **SCM-01**: Trusted dependency sources.
-   **SCM-02**: Vulnerability management process.
-   **SCM-03**: License compliance.

---

## 8. Technology Stack | 技术栈

### 8.1 Agent Orchestration | Agent 编排

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Workflow Engine** | LangGraph | Stateful, graph-based agent orchestration with conditional routing, parallel execution, and checkpointing |
| **LLM Framework** | LangChain | Unified LLM abstraction, prompt management, tool integration, RAG chains |
| **State Management** | LangGraph Checkpointing | Cross-phase state persistence, conversation memory, assessment context |

### 8.2 Core Stack | 核心技术栈

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Primary development language |
| **Web/API** | FastAPI | Async REST API with auto OpenAPI |
| **Vector DB** | ChromaDB | Chunk-level similarity search |
| **Graph RAG** | LightRAG | Entity-relationship aware retrieval |
| **Embeddings** | sentence-transformers | Vector embeddings for RAG |
| **Parsing** | Docling (primary) + legacy fallback | Multi-format document parsing |
| **LLM Providers** | OpenAI, Ollama | Cloud and local LLM support |

---

## 9. References | 参考与借鉴

-   **LangGraph Documentation**: Reference for stateful agent orchestration, conditional routing, and multi-agent patterns.
-   **LangChain Documentation**: Reference for LLM abstraction, RAG patterns, and tool integration.
-   **NIST SSDF (Secure Software Development Framework)**: Reference for SSDLC phase definitions and security activities.
-   **OWASP SAMM (Software Assurance Maturity Model)**: Reference for security practice areas across the SDLC.
-   **Microsoft SDL**: Reference for security development lifecycle practices.
-   **STRIDE/DREAD**: Reference for threat modeling methodology.

---

## 10. Next Steps | 后续步骤

1.  **LangGraph Integration**: Implement LangGraph state machine with phase agent nodes, conditional edges, and shared state.
2.  **Phase Agent MVP**: Implement Requirements and Design phase agents first (highest Shift-Left value).
3.  **Knowledge Base per Phase**: Build phase-specific knowledge collections (requirements policies, design patterns, coding standards, testing guides, deployment checklists, operations playbooks).
4.  **SAST/DAST Connectors**: Build parsers for common tool output formats (SonarQube, Checkmarx, Burp Suite, OWASP ZAP).
5.  **Cross-Phase Traceability**: Implement finding linkage from threat model → test case → deployment check → monitoring rule.
6.  **Enterprise Integration**: Align with IT on AAD registration and ServiceNow API access.
7.  **Pilot**: Run with 1-2 teams across a full SSDLC cycle to gather feedback.
8.  **Open Source**: Release as "DocSentinel" after MVP stabilization.

---

## 11. Open Questions and Deliverables | 待澄清问题与建议产出

### 11.1 Open Questions | 待澄清问题

-   **LangGraph Workflow Schema**: How to define and persist custom SSDLC workflow configurations?
-   **Phase Agent Granularity**: Should each phase have a single agent or multiple sub-agents (e.g. Design → Threat Modeler + Architecture Reviewer)?
-   **SAST/DAST Integration**: Which tool output formats to support first? Standard SARIF format?
-   **Cross-Phase State**: How much context to carry between phases? Full report or summarized findings?
-   **Report Schema**: Concrete JSON schema for phase-specific and cross-phase findings?
-   **Skill Contract**: Input/output for the first phase-specific Skills?
-   **KB Partitioning**: Separate vector collections per SSDLC phase or unified with metadata filtering?
-   **Limits**: File size, concurrency, rate limits per phase?

### 11.2 Recommended Deliverables | 建议产出文档

1.  **Technology & Architecture**: `docs/01-architecture-and-tech-stack.md`
2.  **API Specification**: `docs/02-api-specification.yaml`
3.  **Report & Skill Contract**: `docs/03-assessment-report-and-skill-contract.md`
4.  **Integration Guide**: `docs/04-integration-guide.md`
5.  **Deployment Runbook**: `docs/05-deployment-runbook.md`
6.  **Agent Integration (MCP)**: `docs/06-agent-integration.md`
7.  **SSDLC Workflow Guide**: `docs/07-ssdlc-workflow-guide.md` *(new)*
8.  **Security Implementation**: `SECURITY.md` and secure coding guidelines.

---

**End of Document**
