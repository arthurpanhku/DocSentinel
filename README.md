<p align="center">
  <img src="docs/images/arthor-agent-mascot.png" width="200" alt="Arthor Agent mascot"/>
</p>

<p align="center">
  <strong>Arthor Agent</strong><br/>
  <em>Automated security assessment for documents and questionnaires</em><br/>
  <em>面向文档与问卷的自动化安全评估</em>
</p>

<p align="center">
  <a href="https://github.com/arthurpanhku/Arthor-Agent/releases"><img src="https://img.shields.io/github/v/release/arthurpanhku/Arthor-Agent?include_prereleases" alt="Latest release"/></a>
  <a href="https://github.com/arthurpanhku/Arthor-Agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"/></a>
  <a href="https://github.com/arthurpanhku/Arthor-Agent"><img src="https://img.shields.io/badge/GitHub-arthurpanhku%2FArthor--Agent-24292e?logo=github" alt="GitHub repo"/></a>
  <a href="docs/06-agent-integration.md"><img src="https://img.shields.io/badge/MCP-Ready-green?logo=anthropic" alt="MCP Ready"/></a>
  <a href="docs/06-agent-integration.md"><img src="https://img.shields.io/badge/Agent-Integration-blueviolet" alt="Agent Integration"/></a>
</p>

---

## What is Arthor Agent? | Arthor Agent 是什么？

**Arthor Agent** 是面向安全团队的 AI 助手。它自动化审阅与安全相关的**文档、表格和报告**（如安全问卷、设计文档、合规证据），结合策略与知识库进行比对，并产出**结构化评估报告**，包含风险项、合规差距与整改建议。

🚀 **Agent Ready**: 支持 **Model Context Protocol (MCP)**，可作为“技能”被 OpenClaw、Claude Desktop 等智能体直接调用。

- **多格式输入**：PDF、Word、Excel、PPT、文本，解析为统一格式供大模型使用。
- **知识库（RAG）**：上传策略与合规文档，评估时作为参考检索。
- **多模型支持**：通过统一接口使用 OpenAI、Claude、千问或 **Ollama**（本地）。
- **结构化输出**：JSON/Markdown 报告，含风险项、合规差距与可执行整改建议。

适合需要在大量项目中扩展安全评估、而人力有限的企业。

**Arthor Agent** is an AI-powered assistant for security teams. It automates the review of security-related **documents, forms, and reports** (e.g. Security Questionnaires, design docs, compliance evidence), compares them against your policy and knowledge base, and produces **structured assessment reports** with risks, compliance gaps, and remediation suggestions.

🚀 **Agent Ready**: Supports **Model Context Protocol (MCP)** to be used as a "skill" by OpenClaw, Claude Desktop, and other autonomous agents.

- **Multi-format input**: PDF, Word, Excel, PPT, text — parsed into a unified format for the LLM.
- **Knowledge base (RAG)**: Upload policy and compliance documents; the agent uses them as reference when assessing.
- **Multiple LLMs**: Use OpenAI, Claude, Qwen, or **Ollama** (local) via a single interface.
- **Structured output**: JSON/Markdown reports with risk items, compliance gaps, and actionable remediations.

Ideal for enterprises that need to scale security assessments across many projects without proportionally scaling headcount.

---

## Why Arthor Agent? | 为什么用 Arthor Agent？

| 痛点 (Pain Point)                                                                                    | Arthor Agent 的应对 (Solution)                                                                               |
| :--------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **评估依据分散** / **Fragmented criteria**<br>策略、标准与先例散落各处。                             | 统一**知识库**承载策略与控制项，评估一致、可追溯。<br>Single **knowledge base** ensures consistent findings. |
| **问卷流程繁重** / **Heavy questionnaire workflow**<br>业务填表 → 安全评估 → 业务补证据 → 安全再审。 | **自动化初评**与差距分析，减少多轮往返。<br>**Automated first-pass** reduces manual rounds.                  |
| **上线前审阅压力** / **Pre-release review pressure**<br>安全需审阅并签批大量技术文档。               | **结构化报告**让审阅聚焦决策，而非逐行阅读。<br>**Structured reports** focus on decisions, not reading.      |
| **规模与一致性** / **Scale vs. consistency**<br>项目多、标准多，人工易不一致或延迟。                 | **可配置场景**与统一流水线，保证一致与可审计。<br>**Unified pipeline** keeps assessments consistent.         |

*完整问题陈述与产品目标见 [SPEC.md](./SPEC.md)（产品需求与规格）。*  
*See the full problem statement and product goals in [SPEC.md](./SPEC.md).*

---

## Architecture | 架构

Arthor Agent 以**编排器**为核心，协调解析、知识库（RAG）、技能（如问卷与策略比对）与 LLM。可按环境选用云端或本地大模型，以及可选集成（如 AAD、ServiceNow）。

Arthor Agent is built around an **orchestrator** that coordinates parsing, the knowledge base (RAG), skills, and the LLM. You can use cloud or local LLMs and optional integrations (e.g. AAD, ServiceNow) as your environment requires.

```mermaid
flowchart TB
    subgraph User["👤 User / Security Staff | 用户"]
    end
    subgraph Access["Access Layer | 接入层"]
        API["REST API / MCP"]
    end
    subgraph Core["Arthor Agent Core | 核心"]
        Orch["Orchestrator | 编排"]
        Mem["Memory | 记忆"]
        Skill["Skills | 技能"]
        KB["Knowledge Base (RAG) | 知识库"]
        Parser["Parser | 解析"]
    end
    subgraph LLM["LLM Layer | 大模型层"]
        Abst["LLM Abstraction | LLM 抽象"]
    end
    subgraph Backends["LLM Backends | 后端"]
        Cloud["OpenAI / Claude / Qwen"]
        Local["Ollama / vLLM"]
    end

    User --> API
    API --> Orch
    Orch <--> Mem
    Orch --> Skill
    Orch --> KB
    Orch --> Parser
    Orch --> Abst
    Abst --> Cloud
    Abst --> Local
```

**数据流（简要）| Data flow (simplified):**

1.  用户上传文档，可选选择场景或项目。 / User uploads documents and selects scenario.
2.  **Parser 解析器**将文件（PDF、Word、Excel、PPT 等）转为统一文本/Markdown。 / **Parser** converts files to text/Markdown.
3.  **编排器**从**知识库**（RAG）加载相关片段并调用**技能**。 / **Orchestrator** loads **KB** chunks (RAG) and invokes **Skills**.
4.  **LLM**（OpenAI、Ollama 等）生成结构化结论。 / **LLM** produces structured findings.
5.  返回**评估报告**（风险、合规差距、整改建议）。 / Returns **assessment report** (risks, gaps, remediations).

*详细架构与组件说明见 [ARCHITECTURE.md](./ARCHITECTURE.md) 与 [docs/01-architecture-and-tech-stack.md](./docs/01-architecture-and-tech-stack.md)。*  
*Detailed architecture: [ARCHITECTURE.md](./ARCHITECTURE.md) and [docs/01-architecture-and-tech-stack.md](./docs/01-architecture-and-tech-stack.md).*

---

## Features | 功能概览

| 领域 (Area)                     | 能力 (Capabilities)                                                                                                        |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------- |
| **文档解析** / **Parsing**      | Word、PDF、Excel、PPT、文本 → Markdown/JSON。                                                                              |
| **知识库** / **Knowledge Base** | 多格式上传、分块、向量化（Chroma）、RAG 检索。<br>Multi-format upload, chunking, RAG query.                                |
| **评估** / **Assessment**       | 提交文件 → 获得结构化报告（风险项、合规差距、整改建议）。<br>Submit files → structured report (risks, gaps, remediations). |
| **LLM**                         | 可配置提供商：**Ollama**（本地）、OpenAI 等。<br>Configurable provider: Ollama (local), OpenAI, etc.                       |
| **API**                         | REST API & **MCP Server** for Agent integration.                                                                           |
| **安全与合规** / **Security**   | 内置 **RBAC**、**审计日志**与 **Prompt Injection** 防护。<br>Built-in RBAC, Audit Logs, and Prompt Injection guards.       |
| **Agent集成** / **Integration** | 支持 **MCP**，可被 OpenClaw、Claude Desktop 等智能体调用。<br>Supports **MCP** for OpenClaw, Claude Desktop, etc.          |

路线图（如 AAD/SSO、ServiceNow 集成）见 [SPEC.md](./SPEC.md)。

---

## Quick Start | 快速开始

### Option A: One-Click Deployment (Recommended) | 一键部署（推荐）

Run the deployment script to start the full stack (API + Dashboard + Vector DB + optional Ollama).
运行部署脚本以启动全栈服务（API + 仪表盘 + 向量库 + 可选 Ollama）。

```bash
git clone https://github.com/arthurpanhku/Arthor-Agent.git
cd Arthor-Agent
chmod +x deploy.sh
./deploy.sh
```

-   **Dashboard**: [http://localhost:8501](http://localhost:8501)
-   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option B: Docker Manual

**前置 Prerequisites**: **Python 3.10+**. Optional: [Ollama](https://ollama.ai) (`ollama pull llama2`).

```bash
git clone https://github.com/arthurpanhku/Arthor-Agent.git
cd Arthor-Agent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit if needed: LLM_PROVIDER=ollama or openai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

-   **API docs**: [http://localhost:8000/docs](http://localhost:8000/docs) · **Health**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 示例：提交评估 | Example: submit an assessment

可使用仓库内 [examples/](examples/) 下的示例文件快速试跑。
You can use the sample files in [examples/](examples/) to try the API.

```bash
# 使用示例文本 / Use sample file from repo
curl -X POST "http://localhost:8000/api/v1/assessments" \
  -F "files=@examples/sample.txt" \
  -F "scenario_id=default"

# 响应：{ "task_id": "...", "status": "accepted" } — 用返回的 task_id 查询结果
# Get the result (replace TASK_ID with the returned task_id)
curl "http://localhost:8000/api/v1/assessments/TASK_ID"
```

### 示例：上传知识库并检索 | Example: upload to KB and query

```bash
# 使用示例策略文件 / Use sample policy from repo
curl -X POST "http://localhost:8000/api/v1/kb/documents" -F "file=@examples/sample-policy.txt"

# 检索（RAG）/ Query the KB (RAG)
curl -X POST "http://localhost:8000/api/v1/kb/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the access control requirements?", "top_k": 5}'
```

---

## Project layout | 项目结构

```text
Arthor-Agent/
├── app/                  # 应用代码
│   ├── api/              # REST 路由：评估、知识库、健康检查
│   ├── agent/            # 编排与评估流水线
│   ├── core/             # 配置 (pydantic-settings)
│   ├── kb/               # 知识库 (Chroma, 分块, RAG)
│   ├── llm/              # LLM 抽象 (OpenAI, Ollama)
│   ├── parser/           # 文档解析 (PDF, Word, Excel, PPT, 文本)
│   ├── models/           # Pydantic 模型
│   └── main.py
├── tests/                # 自动化测试 (pytest)
├── examples/             # 示例文件（问卷、策略样本）
├── docs/                 # 设计与规格文档
│   ├── 01-architecture-and-tech-stack.md
│   ├── 02-api-specification.yaml
│   ├── 03-assessment-report-and-skill-contract.md
│   ├── 04-integration-guide.md
│   ├── 05-deployment-runbook.md
│   └── schemas/
├── .github/              # Issue/PR 模板、CI (Actions)
├── Dockerfile
├── docker-compose.yml    # 仅 API
├── docker-compose.ollama.yml  # API + Ollama 可选
├── CONTRIBUTING.md       # 贡献指南
├── CODE_OF_CONDUCT.md    # 行为准则
├── CHANGELOG.md
├── SPEC.md
├── LICENSE
├── SECURITY.md
├── requirements.txt
├── requirements-dev.txt  # 测试与开发依赖
├── pytest.ini
└── .env.example
```

---

## Configuration | 配置

| 变量 Variable                                  | 说明 Description     | 默认 Default                        |
| :--------------------------------------------- | :------------------- | :---------------------------------- |
| `LLM_PROVIDER`                                 | `ollama` 或 `openai` | `ollama`                            |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL`             | 本地 LLM             | `http://localhost:11434` / `llama2` |
| `OPENAI_API_KEY` / `OPENAI_MODEL`              | OpenAI               | —                                   |
| `CHROMA_PERSIST_DIR`                           | 向量库路径           | `./data/chroma`                     |
| `UPLOAD_MAX_FILE_SIZE_MB` / `UPLOAD_MAX_FILES` | 上传限制             | `50` / `10`                         |

*完整选项见 [.env.example](./.env.example) 与 [docs/05-deployment-runbook.md](./docs/05-deployment-runbook.md)。*  
*See [.env.example](./.env.example) and [docs/05-deployment-runbook.md](./docs/05-deployment-runbook.md) for full options.*

---

## Documentation and PRD | 文档与规格

-   **[ARCHITECTURE.md](./ARCHITECTURE.md)** — System architecture: high-level diagram, Mermaid views, component design, data flow, security.<br>系统架构：高层图、Mermaid 视图（逻辑/组件/时序/集成/部署）、组件设计、数据流、安全架构。
-   **[SPEC.md](./SPEC.md)** — Product requirements: problem statement, solution, features, security controls.<br>产品需求与规格：问题陈述、方案、架构摘要、功能、安全控制与开放问题。
-   **[CHANGELOG.md](./CHANGELOG.md)** — Version history; [Releases](https://github.com/arthurpanhku/Arthor-Agent/releases).<br>版本历史；发布说明。
-   **Design docs** [docs/](./docs/)：Architecture, API spec (OpenAPI), contracts, integration guides (AAD, ServiceNow), deployment runbook. Q1 Launch Checklist: [docs/LAUNCH-CHECKLIST.md](./docs/LAUNCH-CHECKLIST.md).<br>架构与技术栈、API 规范、评估报告与 Skill 契约、集成指南、部署手册。Q1 发布清单：[docs/LAUNCH-CHECKLIST.md](./docs/LAUNCH-CHECKLIST.md)。

---

## Contributing | 参与贡献

**English**: Issues and Pull Requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, and commit guidelines. By participating you agree to the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

🤖 **AI-Assisted Contribution**: We encourage using AI tools to contribute! Check out [CONTRIBUTING_WITH_AI.md](CONTRIBUTING_WITH_AI.md) for best practices.

**中文**：欢迎提交 Issue 与 Pull Request。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发环境、测试与提交规范。参与即视为同意 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 行为准则。

🤖 **AI 辅助贡献**：我们也鼓励使用 AI 工具参与贡献！请查看 [CONTRIBUTING_WITH_AI.md](CONTRIBUTING_WITH_AI.md) 获取最佳实践指南。

---

## Security | 安全

-   **漏洞报告 / Vulnerability reporting**：负责任披露请见 [SECURITY.md](./SECURITY.md)。<br>See [SECURITY.md](./SECURITY.md) for responsible disclosure.
-   **安全需求 / Security requirements**：项目遵循 [SPEC §7.2](./SPEC.md) 中定义的安全控制（身份、数据保护、应用安全、运维、供应链）。<br>Follows security controls in [SPEC §7.2](./SPEC.md).

---

## License | 许可证

本项目采用 **MIT License**，详见 [LICENSE](./LICENSE) 文件。<br>This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=arthurpanhku/Arthor-Agent&type=Date)](https://star-history.com/#arthurpanhku/Arthor-Agent&Date)

---

## Author and links | 作者与链接

-   **作者 Author**: PAN CHAO (Arthur Pan)
-   **仓库 Repository**: [github.com/arthurpanhku/Arthor-Agent](https://github.com/arthurpanhku/Arthor-Agent)
-   **规格与设计文档 SPEC and design docs**: 见上文链接。See links above.

若你在组织中使用 Arthor Agent 或希望参与贡献，欢迎通过 GitHub Discussions 或 Issues 联系我们。<br>If you use Arthor Agent in your organization or contribute back, we’d love to hear from you (e.g. via GitHub Discussions or Issues).
