# Design and Specification Index | 设计与规范文档目录

This directory holds **executable design and specification** artifacts that accompany the PRD for development, integration, and operations.

本目录存放与 PRD（产品需求文档）配套的**可执行设计与规范**，供开发、集成与运维使用。

**PRD Location**: [`../SPEC.md`](../SPEC.md)

---

## Document List | 文档列表

| ID     | Document                                                                             | Purpose                                                             | Timing               |
| :----- | :----------------------------------------------------------------------------------- | :------------------------------------------------------------------ | :------------------- |
| **01** | [Architecture and Tech Stack](./01-architecture-and-tech-stack.md)                   | Technology choices, high-level architecture, interfaces, data flow. | Start / Design Phase |
| **02** | [API Specification](./02-api-specification.yaml)                                     | REST API Contract (OpenAPI 3.x).                                    | Parallel with 01     |
| **03** | [Assessment Report and Skill Contract](./03-assessment-report-and-skill-contract.md) | JSON Schemas for Reports and Skills.                                | Pre-Development      |
| **04** | [Integration Guide](./04-integration-guide.md)                                       | AAD, ServiceNow configuration and mapping.                          | Integration Phase    |
| **05** | [Deployment Runbook](./05-deployment-runbook.md)                                     | Deployment, config reference, ops.                                  | Pre-Release          |
| **06** | [Agent Integration (MCP)](./06-agent-integration.md)                                 | MCP setup for Claude Desktop, Cursor, OpenClaw.                     | Integration Phase    |

---

## Default Tech Stack | 技术栈默认假设

Aligned with PRD and current implementation:

-   **Language**: Python 3.10+
-   **Web/API**: FastAPI + MCP Server (stdio)
-   **Agent**: LangChain + LangGraph (stateful graph-based orchestration with SSDLC routing)
-   **SSDLC**: 6-stage pipeline (Requirements → Design → Development → Testing → Deployment → Operations)
-   **Vector DB**: Chroma (+ LightRAG for Graph RAG)
-   **Parsing**: Docling (primary) + PyMuPDF, python-docx, openpyxl (legacy fallback)
-   **LLM**: LangChain Abstraction (OpenAI / Ollama)

*See [01-architecture-and-tech-stack.md](./01-architecture-and-tech-stack.md) for details.*

---

## How to Use | 使用方式

1.  **Start with 01**: Confirm stack and architecture.
2.  **Sync 02**: Use FastAPI to generate OpenAPI or write YAML first.
3.  **Validate 03**: Use `schemas/assessment-report.json` for validation.
4.  **Refine 04/05**: Update when integrating with real environments.

### Directory Structure

```text
docs/
├── README.md
├── 01-architecture-and-tech-stack.md
├── 02-api-specification.yaml
├── 03-assessment-report-and-skill-contract.md
├── 04-integration-guide.md
├── 05-deployment-runbook.md
├── 06-agent-integration.md
└── schemas/
    └── assessment-report.json
```
