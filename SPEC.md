# DocSentinel — Product Requirements Document (PRD) | 产品需求文档

|             |                         |
| :---------- | :---------------------- |
| **Version** | v4.0                    |
| **Date**    | 2026-03-29              |
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

-   **v4.0**: SSDLC + LangGraph. Full SSDLC lifecycle support (6 stages), LangChain/LangGraph as orchestration engine, stage-specific skills and assessment flows.
    SSDLC + LangGraph。完整 SSDLC 生命周期支持（6 阶段），引入 LangChain/LangGraph 作为编排引擎，阶段专属 Skill 与评估流程。
-   **v3.1**: Performance & quality. Graph RAG, Docling parser, async pipeline, parallel orchestration, guardrails, singleton KB, cached LLM.
    性能与质量优化。Graph RAG、Docling 解析器、异步流水线、并行编排、输入防护、单例 KB、缓存 LLM。
-   **v3.0**: Headless pivot. Removed Streamlit frontend; pure API + MCP service.
    无前端化转型。移除 Streamlit 前端，纯 API + MCP 服务。
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

This PRD is for the open-source "DocSentinel" project. It defines business pain points, solution approach, system architecture, and product scope to serve as a single source of truth for subsequent design and development. The project aims to use an AI Agent to automate the review of and recommendations for security-related documents, forms, and reports, reduce the burden on enterprise security teams, and support integration with mainstream and local LLMs, multi-format file parsing, and extensible Skills and knowledge bases. Starting from v4.0, DocSentinel provides **full SSDLC (Secure Software Development Lifecycle) coverage**, supporting automated assessment at every stage — from requirements and design through development, testing, deployment, and operations — powered by **LangChain and LangGraph** as the agent orchestration framework.

**中文**

本 PRD 面向「DocSentinel」开源项目，用于明确业务痛点、解决方案、系统架构与产品范围，为后续设计与开发提供统一依据。项目目标是通过 AI Agent 自动化完成安全评估相关文档/表格/报告的审阅与建议，减轻企业安全团队负担，并支持对接主流与本地大模型、多格式文件解析及可扩展的 Skill 与知识库。自 v4.0 起，DocSentinel 提供**完整的 SSDLC（安全软件开发生命周期）覆盖**，支持从需求、设计、开发、测试、部署到运维每个阶段的自动化评估，并引入 **LangChain 与 LangGraph** 作为 Agent 编排框架。

---

## 2. Business Context and Pain Points | 业务背景与痛点

### 2.1 Business Context | 业务背景

**English**

Enterprise Cyber Security teams operate under multiple constraints:

-   **Diverse reference sources**: Internal security policies, industry best practices (e.g. NIST SSDF, OWASP, CISA), past project cases, and compliance frameworks (e.g. SOC2, ISO 27001).
-   **Full SSDLC coverage**: Security review and control requirements exist at every stage—requirements/design, development, testing, deployment, and operations.
-   **Wide variety of deliverables**: Security questionnaires, design documents, threat models, SAST/DAST reports, compliance evidence, and audit materials all require manual reading, comparison, and sign-off.

In agile and DevOps environments, enterprises ship dozens to hundreds of projects per year. Security teams must complete large volumes of assessments and reviews with limited headcount, creating a clear bottleneck.

**中文**

大型企业的 Cyber Security 团队需要在以下多维度约束下工作：

-   **依据来源多样**：公司内部 Security Policy、行业最佳实践（如 NIST SSDF、OWASP、CISA 等）、历史项目案例与合规框架（如 SOC2、ISO 27001）。
-   **流程覆盖完整 SSDLC**：从需求/设计、开发、测试、部署到运维，每个阶段都有安全评审与管控要求。
-   **交付物类型繁多**：安全问卷（Security Questionnaire）、设计文档、威胁建模、SAST/DAST 报告、合规证明、审计材料等，需人工阅读、比对与签字（Sign-off）。

在敏捷与 DevOps 环境下，企业每年上线项目数量从几十到几百不等，安全人员需要在有限人力下完成大量评估与审阅，成为明显瓶颈。

### 2.2 Core Pain Points | 核心痛点

| Pain Point (English)                                                                                                                                                     | 痛点描述 (中文)                                                                        |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------- |
| **Fragmented assessment criteria**<br>Teams must align with policies, industry standards, and project precedents; manual lookup and alignment cost is high.              | **评估依据分散**<br>需同时参照 Policy、行业标准、项目案例；人工查找与对齐成本高。      |
| **Heavy questionnaire workflow**<br>Multiple rounds of questionnaire filling, assessment, evidence collection, and review; inconsistent templates.                       | **问卷与证据流程繁重**<br>问卷—评估—证据—审阅多轮往返；模板不统一、证据质量参差。      |
| **Development-phase control relies on people**<br>Policy definition, result interpretation, and exception approval still depend on security staff and are hard to scale. | **开发阶段管控依赖人工**<br>策略制定、结果解读、例外审批仍依赖安全人员，难以规模化。   |
| **Pre-release review pressure**<br>Security must review every file and sign off. Technical documents are hard for non-technical staff to interpret.                      | **上线前集中审阅压力大**<br>需 Review 全部文件并 Sign-off；技术文档阅读与理解成本高。  |
| **Scale vs. consistency**<br>Manual assessment tends to be inconsistent, incomplete, or delayed; reusable patterns are hard to institutionalize.                         | **规模与一致性矛盾**<br>人工评估易出现不一致、遗漏或延迟，且难以沉淀可复用的评估模式。 |
| **SSDLC coverage gaps**<br>Security involvement is unevenly distributed across the SSDLC; requirements and design phases often get less scrutiny than pre-release review, leaving risks to accumulate. | **SSDLC 覆盖断层**<br>安全介入在 SSDLC 各阶段分布不均；需求与设计阶段审查不足，风险层层积累到上线前集中爆发。 |

### 2.3 Desired Change | 期望改变

-   **Automation / 自动化**: Automate analysis and initial assessment of forms, documents, and reports to reduce repetitive manual reading.
-   **Consistency / 一致性**: Produce consistent assessment conclusions and remediation recommendations based on a unified knowledge base and policies.
-   **Extensibility / 可扩展**: Support assessment scenarios for different compliance frameworks and customer/project types.
-   **SSDLC coverage / 全生命周期覆盖**: Provide stage-aware assessment across the entire SSDLC — requirements, design, development, testing, deployment, and operations — with stage-specific skills and checklists.

---

## 3. Solution Overview | 解决方案概述

### 3.1 Product Positioning | 产品定位

**English**

Build a **dedicated AI Agent for security teams**, with the primary focus on **automating the assessment of all forms, documents, and reports that require security team review across the entire Secure Software Development Lifecycle (SSDLC)**. After security staff submit project-related files to the Agent, the Agent will:

1.  **Parse multi-format files**: Convert Word, PDF, Excel, PPT, images, etc. into an intermediate format (e.g. JSON/Markdown).
2.  **Use knowledge base and policy**: Rely on built-in or configurable compliance and policy knowledge to understand "what standards must be met."
3.  **SSDLC-aware assessment**: Automatically determine or accept the SSDLC stage (Requirements, Design, Development, Testing, Deployment, Operations) and apply stage-specific assessment logic, checklists, and risk focus.
4.  **Perform risk assessment and recommendations**: Identify security/compliance risks and provide security advice and actionable remediation.
5.  **Produce structured output**: Enable security staff to quickly review, sign off, or hand off to business/development for remediation.

**中文**

构建**安全团队专用 AI Agent**，首要方向为：**自动化评估所有需要安全团队审阅的表格、文档与报告，覆盖完整的安全软件开发生命周期（SSDLC）**。安全人员将项目相关文件提交给 Agent 后，Agent 能够：

1.  **解析多格式文件**：将 Word、PDF、Excel、PPT、图片等转为可被模型理解的中间格式（如 JSON/Markdown）。
2.  **结合知识库与策略**：基于内置/可配置的合规与策略知识库，理解「应该满足什么标准」。
3.  **SSDLC 阶段感知评估**：自动识别或接受 SSDLC 阶段（需求、设计、开发、测试、部署、运维），应用阶段专属评估逻辑、检查清单和风险关注点。
4.  **执行风险评估与建议**：识别与安全/合规相关的风险点，给出安全建议与可操作的整改方案。
5.  **输出结构化结果**：便于安全人员快速复核、签字或转交业务/开发团队整改。

### 3.2 Solution Value | 方案价值

-   **Cost reduction / 降本**: Reduce time security staff spend on repetitive document review.
-   **Speed / 提速**: Shorten the questionnaire → assessment → evidence → review cycle.
-   **Reproducibility / 可复现**: Assessment logic and criteria can be captured in the knowledge base and Skills.
-   **Openness / 开放**: Support multiple commercial and local LLMs to meet requirements for data residency and cost control.

---

## 4. Product Goals and Success Metrics | 产品目标与成功指标

### 4.1 Product Goals | 产品目标

| Goal                                         | Description                                                                                                                                            |
| :------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Automated assessment**<br>自动化评估       | Support automatic parsing and risk assessment of common formats for security questionnaires, design documents, compliance evidence, and audit reports. |
| **Configurable scenarios**<br>可配置评估场景 | Use the knowledge base and Skills to configure different assessment criteria and check items by compliance framework, customer type, or project type.  |
| **Multi-model support**<br>多模型支持        | Support mainstream commercial LLMs (e.g. ChatGPT, Qwen, Claude) and local/on-prem models (e.g. Ollama) through a unified interface.                    |
| **Actionable results**<br>结果可操作         | Output risk items, compliance gaps, concrete remediation suggestions, and (optionally) priority.                                                       |
| **SSDLC lifecycle**<br>SSDLC 全生命周期     | Cover all 6 SSDLC stages (Requirements, Design, Development, Testing, Deployment, Operations) with stage-specific skills, checklists, and flows.       |

### 4.2 Success Metrics (Suggested) | 成功指标（建议）

-   **Coverage**: Number of supported document types (e.g. 5+ common formats) and knowledge base entries.
-   **Efficiency**: Average time from upload to report generation; time saved vs. manual review.
-   **Usability**: Steps and time to complete one "upload → view report → make decision" loop.
-   **Extensibility**: Configuration/development cost to add a new file type or assessment scenario.

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

The system uses a layered design: **Access** (REST API / MCP Server) → **Core** (Orchestrator, SSDLC Pipeline, Memory, Skills, Knowledge Base RAG, Parser) → **LLM abstraction** → **Cloud/local LLMs**. The orchestrator is built on **LangChain + LangGraph**, enabling stateful, graph-based agent workflows with conditional branching per SSDLC stage. Optional integrations: **AAD** (identity/SSO) and **ServiceNow** (project metadata).

**中文**

系统采用分层设计：**接入层**（REST API / MCP Server）→ **核心**（任务编排、SSDLC 流水线、记忆体、Skill 层、知识库 RAG、文件解析）→ **LLM 抽象层** → **商用/本地 LLM**。编排引擎基于 **LangChain + LangGraph** 构建，支持有状态、图驱动的 Agent 工作流与 SSDLC 阶段条件分支。可选对接 **AAD**（身份/SSO）与 **ServiceNow**（项目元数据）。

**High-Level Diagram | 架构图**

```text
                    ┌─────────────────────────────────────────────────────────┐
                    │           User / Security Staff | 用户 / 安全人员         │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
                    ┌───────────────────────────▼─────────────────────────────┐
                    │             Access Layer | 接入层 (API / MCP)           │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
    ┌───────────────────────────────────────────▼───────────────────────────────────────────┐
    │                         DocSentinel Core | 核心                                      │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
    │  │ Orchestrator│  │   Memory    │  │   Skills    │  │ KB (RAG)    │  │   Parser   │  │
    │  │  任务编排    │  │   记忆体     │  │   Skill 层  │  │   知识库     │  │  文件解析   │  │
    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬───────┘  │
    │         │                │                │                │                │          │
    │         └────────────────┴────────────────┴────────────────┴────────────────┘          │
    │                                          │                                               │
    │                              ┌───────────▼───────────┐                                  │
    │                              │  LLM Abstraction Layer│                                  │
    │                              └───────────┬───────────┘                                  │
    └──────────────────────────────────────────┼──────────────────────────────────────────────┘
                                               │
        ┌─────────────────────────────────────┼─────────────────────────────────────┐
        │  Commercial/Cloud LLM               │    Local/On-prem LLM                │
        │  ChatGPT / Claude / Qwen / Gemini   │    Ollama / vLLM / ...              │
        └─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Component Index | 核心组件索引

| Component           | Role                                                      | Details                              |
| :------------------ | :-------------------------------------------------------- | :----------------------------------- |
| **Orchestrator**    | LangGraph-based stateful agent graph; coordinates Parser, KB, Skills, LLM. | ARCHITECTURE.md § Component Design   |
| **SSDLC Pipeline**  | Stage-aware routing (6 stages); selects stage-specific skills and checklists. | ARCHITECTURE.md § SSDLC Pipeline     |
| **Memory**          | Manages working, episodic, and semantic memory.           | ARCHITECTURE.md § Component Design   |
| **Skills**          | Reusable assessment capabilities (e.g. policy check, SSDLC stage skills). | ARCHITECTURE.md § Component Design   |
| **Knowledge Base**  | Multi-format ingestion, chunking, embedding, RAG.         | ARCHITECTURE.md § Component Design   |
| **Parser**          | Converts files (PDF, Word, Excel, etc.) to Markdown/JSON. | ARCHITECTURE.md § Component Design   |
| **LLM Abstraction** | Unified interface for model switching.                    | ARCHITECTURE.md § Component Design   |
| **Integrations**    | AAD (SSO), ServiceNow (metadata).                         | ARCHITECTURE.md § Integration Points |

### 5.3 Data Flow (Summary) | 数据流（简要）

1.  User submits **assessment task** (files + optional SSDLC stage / skill ID) via API or MCP. API returns `task_id` immediately (non-blocking).
2.  **Parser** converts files to intermediate Markdown/text format (Docling or legacy).
3.  **SSDLC Router** determines the lifecycle stage (auto-detect or user-specified) and selects stage-specific skill + checklist.
4.  **LangGraph Orchestrator** executes the agent graph: Policy+History and Evidence nodes run **in parallel**, followed by Drafter and Reviewer nodes.
5.  Structured **assessment report** (risks, gaps, remediations, confidence, sources, SSDLC stage) is stored.
6.  User polls `GET /assessments/{task_id}` to retrieve the completed report.

---

## 6. Scope and User Stories | 功能范围与用户故事

### 6.1 Core Feature List | 核心功能列表

| Module             | Feature                                                                 | Priority |
| :----------------- | :---------------------------------------------------------------------- | :------- |
| **Parser**         | Upload Word / PDF / Excel / PPT and convert to JSON/Markdown.           | P0       |
| **Parser**         | OCR / Vision support for images.                                        | P1       |
| **Knowledge Base** | Upload multi-format docs, parse, chunk, embed, and retrieve (RAG).      | P0       |
| **Knowledge Base** | Metadata filtering (e.g. by framework, customer).                       | P1       |
| **Assessment**     | Select scenario, upload files, trigger assessment.                      | P0       |
| **Assessment**     | Output structured report (Risks, Gaps, Remediation, **Confidence**).    | P0       |
| **Assessment**     | **Human-in-the-Loop**: Review, approve, reject, comment workflow.       | P0       |
| **LLM**            | Configurable commercial LLMs (OpenAI, Claude, etc.).                    | P0       |
| **LLM**            | Configurable local models (Ollama).                                     | P0       |
| **Skill**          | **Skill/Persona Management**: Create custom roles and import templates. | P0       |
| **Skill**          | Built-in personas (e.g. SOC2 Auditor, AppSec Engineer).                 | P0       |
| **Orchestrator**   | **LangGraph**: Stateful graph-based agent orchestration with conditional branching. | P0       |
| **SSDLC**          | **Requirements Stage**: Security requirements, compliance mapping, threat modeling inputs. | P0       |
| **SSDLC**          | **Design Stage**: Security architecture review, STRIDE/DREAD, encryption/permission design, SDR. | P0       |
| **SSDLC**          | **Development Stage**: Secure coding standards, built-in controls (anti-injection, XSS). | P0       |
| **SSDLC**          | **Testing Stage**: SAST/DAST report review, penetration test findings, vulnerability verification. | P0       |
| **SSDLC**          | **Deployment Stage**: Release readiness review, config security, key management, hardening. | P0       |
| **SSDLC**          | **Operations Stage**: Vulnerability monitoring, incident response, patch management, log audit. | P0       |
| **SSDLC**          | **Auto-detect stage** from document content or accept explicit stage parameter.   | P1       |
| **Memory**         | **History Reuse**: Retrieve past similar answers.                       | P1       |
| **Access**         | REST API + MCP Server.                                                  | P0       |
| **Integrations**   | ServiceNow: Read project metadata.                                      | P0       |
| **Integrations**   | ServiceNow: Write back results / Webhook trigger.                       | P1       |
| **IAM**            | AAD (Azure AD) Login & SSO.                                             | P0       |
| **IAM**            | RBAC (Analyst, Lead, Project Owner, Admin, API Consumer).               | P0       |
| **IAM**            | API Authentication (Bearer Token / API Key).                            | P0       |
| **IAM**            | Data isolation by project/role.                                         | P0       |

### 6.2 User Stories (Examples) | 用户故事（示例）

-   **As a security team member**, I want to upload a Security Questionnaire (Excel/Word) and an architecture document (PDF) **so that** the Agent can automatically identify gaps vs. policy/standards and suggest remediation.
-   **As a security lead**, I want to select or link a project from ServiceNow when starting an assessment **so that** the system auto-fills project type and compliance scope.
-   **As enterprise IT**, I want to configure the Agent to use only a local Ollama model **so that** assessment content never leaves the internal network.
-   **As a developer**, I want to submit documents via REST API and receive assessment results in JSON **so that** the Agent can be integrated into existing ticketing workflows.
-   **As a security architect**, I want to submit a system design document and specify "Design" as the SSDLC stage **so that** the Agent applies STRIDE/DREAD threat modeling and checks encryption/permission design against our standards.
-   **As a DevSecOps engineer**, I want to submit SAST/DAST scan results at the "Testing" stage **so that** the Agent triages findings, maps them to compliance requirements, and prioritizes remediation.
-   **As an operations engineer**, I want to submit incident response logs at the "Operations" stage **so that** the Agent evaluates our response procedures against best practices and identifies process gaps.
-   **As a project manager**, I want the Agent to auto-detect the SSDLC stage from the uploaded document type **so that** I don't need to manually specify it every time.

### 6.3 SSDLC Stage Definitions | SSDLC 阶段定义

The 6 standard SSDLC stages (aligned with NIST, OWASP, and Microsoft SDL):

| Stage | Name (EN) | 阶段名称 (CN) | Key Activities | Typical Inputs |
| :---- | :-------- | :------------ | :------------- | :------------- |
| **1** | **Requirements** | 需求阶段 | Define security requirements, compliance mapping (GDPR, ISO 27001, etc.), initial threat modeling, risk analysis | Requirements docs, compliance checklists, regulatory references |
| **2** | **Design** | 设计阶段 | Security architecture design, permission/access model, encryption scheme, threat modeling (STRIDE/DREAD), Security Design Review (SDR) | Architecture docs, design specs, threat models, data flow diagrams |
| **3** | **Development** | 开发阶段 | Secure coding standards compliance, security training verification, built-in security controls (anti-injection, XSS prevention, input validation) | Source code, coding guidelines, code review reports |
| **4** | **Testing** | 测试阶段 | SAST (static analysis), DAST (dynamic scanning), penetration testing, vulnerability fix & verification | SAST/DAST reports, pen-test findings, vulnerability scan results |
| **5** | **Deployment** | 部署阶段 | Security release readiness review, configuration security (key management, least privilege), hardening checklist | Deployment configs, infrastructure-as-code, release checklists |
| **6** | **Operations** | 运维阶段 | Vulnerability monitoring, incident response evaluation, patch management, log audit, ongoing compliance | Monitoring alerts, incident reports, audit logs, patch records |

Each stage maps to one or more **built-in SSDLC Skills** that define stage-specific `system_prompt`, `risk_focus`, `compliance_frameworks`, and assessment checklists. Users can also create custom SSDLC skills.

---

## 7. Non-Functional Requirements | 非功能需求

### 7.1 General NFRs | 通用非功能需求

| Category               | Requirement (English)                                                                         | 要求 (中文)                                 |
| :--------------------- | :-------------------------------------------------------------------------------------------- | :------------------------------------------ |
| **Security & Privacy** | Support fully local/on-prem deployment and local LLM; support audit logs.                     | 支持纯本地部署与本地 LLM；支持审计日志。    |
| **Performance**        | Acceptable end-to-end latency for a standard assessment (e.g. 10-page PDF + 1 questionnaire). | 单次评估时延可接受（具体目标待定）。        |
| **Maintainability**    | KB, Skills, and LLM config maintainable via config/UI without code changes.                   | 知识库、Skill、LLM 可配置，无需改代码扩展。 |
| **Observability**      | Log model usage, tokens, duration, and errors.                                                | 记录模型、token、耗时与错误。               |
| **Auth & Isolation**   | RBAC and data isolation by project/role; fine-grained auth via AAD/ServiceNow.                | 按角色与项目隔离数据；细粒度授权。          |
| **Deployment**         | Support on-prem/private deployment; connectivity to AAD/ServiceNow/LLM.                       | 支持内网部署；需连通 AAD/ServiceNow/LLM。   |
| **Open Source**        | Architecture aligns with mainstream open-source Agent projects.                               | 架构参考主流开源项目，便于社区贡献。        |

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
-   **IAM-05**: Sensitive operations (e.g. delete KB) require confirmation or higher privilege.

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
-   **OPS-02**: Operational logs (performance, errors) without sensitive content.
-   **OPS-03**: Security event detection and alerting.
-   **OPS-04**: Backup and recovery for critical data.

**7.2.6 Supply Chain | 供应链**

-   **SCM-01**: Trusted dependency sources.
-   **SCM-02**: Vulnerability management process.
-   **SCM-03**: License compliance.

---

## 8. References (Open-Source AI Agent Projects) | 参考与借鉴

-   **Docker Agent (cagent)**: Reference for "pluggable LLM + tools".
-   **VoltAgent AI Agent Platform**: Reference for "production Agent platform" architecture.
-   **GitHub Agentic Workflows**: Reference for "human-in-the-loop" and safety policies.
-   **Agent Memory Architecture**: Reference for layered memory and RAG.

---

## 9. Next Steps | 后续步骤

1.  **Technology Choices**: Finalize Python, LangChain/LangGraph, Vector DB, Parsing libs, LLM SDK.
2.  **MVP Scope**: "One file type + Single KB + One Skill + 1 LLM" end-to-end loop. Then add AAD & ServiceNow.
3.  **Enterprise Integration**: Align with IT on AAD registration and ServiceNow API access.
4.  **Pilot**: Run with 1-2 teams to gather feedback.
5.  **Open Source**: Release as "DocSentinel" after MVP stabilization.

---

## 10. Open Questions and Deliverables | 待澄清问题与建议产出

### 10.1 Open Questions | 待澄清问题

-   **API Contract**: Request/response shape for core APIs?
-   **Report Schema**: Concrete JSON schema for findings?
-   **Skill Contract**: Input/output for the first Skill?
-   **KB Chunking**: Strategy and parameters?
-   **ServiceNow**: Concrete tables/APIs mapping?
-   **Limits**: File size, concurrency, rate limits?
-   **License**: Project license (Apache 2.0 / MIT)?

### 10.2 Recommended Deliverables | 建议产出文档

1.  **Technology & Architecture**: `docs/01-architecture-and-tech-stack.md`
2.  **API Specification**: `docs/02-api-specification.yaml`
3.  **Report & Skill Contract**: `docs/03-assessment-report-and-skill-contract.md`
4.  **Integration Guide**: `docs/04-integration-guide.md`
5.  **Deployment Runbook**: `docs/05-deployment-runbook.md`
6.  **Security Implementation**: `SECURITY.md` and secure coding guidelines.

---

**End of Document**
