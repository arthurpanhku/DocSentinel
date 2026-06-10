# Security Policy | 安全策略

This document covers vulnerability disclosure and security-related practices for the **DocSentinel** project — an AI-powered SSDLC platform. It aligns with [**PRD §7.2 Security Requirements and Controls**](./SPEC.md).

本文档涵盖 **DocSentinel** 项目（AI 驱动的 SSDLC 平台）的漏洞披露与安全实践，遵循 [**PRD §7.2 安全需求与控制**](./SPEC.md)。

---

## Supported Versions | 支持版本

| Version   | Supported          |
| :-------- | :----------------- |
| **4.0.x** | :white_check_mark: |
| **3.1.x** | :white_check_mark: |
| **3.0.x** | :white_check_mark: |
| **2.0.x** | :warning: Limited  |
| < 2.0     | :x:                |

---

## Reporting a Vulnerability | 漏洞报告

If you discover a security vulnerability, please report it responsibly:

1.  **Do not** open a public GitHub issue for security-sensitive findings.
2.  **Email** the maintainers (e.g. the contact in the PRD: `u3638376@connect.hku.hk`) with:
    -   A description of the vulnerability and steps to reproduce.
    -   Impact and suggested fix if possible.
3.  We will acknowledge receipt and aim to respond within a reasonable timeframe. We may ask for more details and will keep you updated on remediation and disclosure.

如果您发现了安全漏洞，请负责任地进行报告：

1.  **请勿**针对敏感安全问题提交公开的 GitHub Issue。
2.  请**发送邮件**给维护者（联系方式见 PRD：`u3638376@connect.hku.hk`），包含：
    -   漏洞描述与复现步骤。
    -   影响范围与建议修复方案（如有）。
3.  我们将在合理时间内确认收到并回复。可能会向您询问更多细节，并同步后续的修复与披露进度。

---

## Security-Related Configuration | 安全相关配置

-   **Secrets**: Do not commit `.env` or any file containing `SECRET_KEY`, API keys, or passwords. Use `.env.example` as a template only.
-   **Input Validation**: File type and size limits are enforced (see `UPLOAD_MAX_FILE_SIZE_MB`, `UPLOAD_MAX_FILES`). Only allowed extensions are parsed (see `app/parser/service.py`).
-   **MCP Document Roots**: `assess_document.file_path` is confined to `MCP_DOCUMENT_ROOTS` before any file read. Configure this to the smallest approved document directory; never expose the MCP server with broad roots such as `/`, a user home directory, or a shared workspace containing secrets.
-   **Prompt Injection Guardrails**: Input sanitization via regex pattern detection and length limits is enforced before content reaches the LLM (see `app/core/guardrails.py`). Malicious inputs are rejected with HTTP 400.
-   **TLS**: In production, use HTTPS and TLS 1.2+ for all endpoints and external calls ([PRD §7.2 DATA-01](./SPEC.md)).
-   **Auth**: API currently does not enforce authentication in the MVP; add AAD/API Key as per [PRD §7.2 IAM](./SPEC.md) before exposing externally.
-   **LangGraph State**: Assessment state and checkpoints may contain sensitive document content. Ensure `LANGGRAPH_CHECKPOINT_DIR` is on encrypted storage in production.
-   **SAST/DAST Integration**: When ingesting scan results from external tools, validate report integrity and source authenticity.

-   **机密信息**：请勿提交 `.env` 或任何包含 `SECRET_KEY`、API Key、密码的文件。`.env.example` 仅作为模板使用。
-   **输入验证**：强制执行文件类型与大小限制（见 `UPLOAD_MAX_FILE_SIZE_MB`、`UPLOAD_MAX_FILES`）。仅解析允许的扩展名（见 `app/parser/service.py`）。
-   **MCP 文档根目录**：`assess_document.file_path` 必须在任何文件读取之前被限制在 `MCP_DOCUMENT_ROOTS` 内。请将该值配置为最小必要的批准文档目录；不要在对外暴露 MCP server 时使用 `/`、用户 home 目录或包含密钥的共享工作区等宽泛根目录。
-   **提示注入防护**：通过正则模式检测和长度限制对输入进行清洗，在内容到达 LLM 之前执行（见 `app/core/guardrails.py`）。恶意输入将被 HTTP 400 拒绝。
-   **TLS**：生产环境中，所有端点与外部调用必须使用 HTTPS 和 TLS 1.2+（[PRD §7.2 DATA-01](./SPEC.md)）。
-   **认证**：MVP 阶段 API 暂未强制认证；在对外暴露前，请根据 [PRD §7.2 IAM](./SPEC.md) 添加 AAD/API Key 认证。
-   **LangGraph 状态**：评估状态和检查点可能包含敏感文档内容。生产环境中请确保 `LANGGRAPH_CHECKPOINT_DIR` 位于加密存储上。
-   **SAST/DAST 集成**：从外部工具接入扫描结果时，请验证报告完整性和来源真实性。

---

## Secure Development Guidelines | 安全开发准则

Use the following principles when adding new API, MCP, parser, KB, or agent features.

新增 API、MCP、Parser、KB 或 Agent 功能时，请遵循以下原则。

### Treat External Inputs as Authority Requests | 将外部输入视为权限请求

Any value controlled by an API client, MCP caller, LLM tool call, browser UI, uploaded file, or environment-adjacent integration is untrusted. Before using it to access local resources, ask:

-   **Who supplied this value?**
-   **Whose authority will execute the action?**
-   **What boundary proves this caller is allowed to do it?**

API client、MCP caller、LLM tool call、浏览器 UI、上传文件或外部集成提供的值都不可信。使用它访问本地资源前，应先问：

-   **这个值是谁提供的？**
-   **实际执行动作的是谁的权限？**
-   **有什么边界能证明调用者被允许这样做？**

### File and Path Handling | 文件与路径处理

File paths are not ordinary strings. A caller-controlled path asks the server process to use server-side filesystem permissions.

-   Resolve paths with `Path.resolve()` or equivalent realpath semantics before access.
-   Check that the resolved path is inside an explicit allow-root such as `MCP_DOCUMENT_ROOTS`.
-   Validate symlink targets after resolution; symlinks must not escape the allow-root.
-   Reject directories, devices, sockets, and other non-regular files.
-   Validate file extension and size before reading content.
-   Never use extension allow-lists as a substitute for directory confinement.
-   Add tests for absolute paths, `..`, symlink escape, unsupported extensions, and missing files.

文件路径不是普通字符串。调用者可控路径意味着调用者请求 server 进程使用 server 端文件系统权限。

-   访问前使用 `Path.resolve()` 或等价 realpath 语义解析路径。
-   检查解析后的路径是否位于显式允许根目录内，例如 `MCP_DOCUMENT_ROOTS`。
-   解析后检查 symlink 目标；symlink 不得逃逸允许根目录。
-   拒绝目录、设备文件、socket 和其他非普通文件。
-   在读取内容前验证扩展名和大小。
-   不要把扩展名白名单当作目录访问控制。
-   为绝对路径、`..`、symlink 逃逸、不支持扩展名和不存在文件添加测试。

### MCP and Agent Tools | MCP 与 Agent 工具

MCP tools are security boundaries because an agent may call them based on user input or prompt-injected instructions.

-   Keep tool scopes narrow and explicit.
-   Prefer IDs, handles, or uploaded document references over arbitrary local paths.
-   If a tool must touch local files, require an allow-root and document the expected configuration.
-   Return minimal error details; do not echo sensitive paths or content.
-   Assume tool output may be visible to the caller and may be copied into an LLM transcript.

MCP 工具是安全边界，因为 agent 可能基于用户输入或 prompt injection 指令调用工具。

-   保持工具作用域小而明确。
-   优先使用 ID、handle 或上传文档引用，而不是任意本地路径。
-   如果工具必须访问本地文件，必须要求允许根目录并记录配置方式。
-   返回最小必要错误信息；不要回显敏感路径或内容。
-   假设工具输出会被调用者看到，也可能进入 LLM transcript。

### LLM Data Flow | LLM 数据流

Anything sent to an LLM provider can leave the local process. Before passing data to the LLM:

-   Confirm the data was intentionally selected by an authorized workflow.
-   Avoid sending secrets, credentials, raw `.env` content, private keys, or unrelated local files.
-   Preserve citations and metadata so generated findings can be audited.
-   Make local-model and private-deployment modes clear for sensitive use cases.

任何发送给 LLM provider 的内容都可能离开本地进程。传给 LLM 前应确认：

-   数据是由授权工作流有意选择的。
-   避免发送密钥、凭据、原始 `.env` 内容、私钥或无关本地文件。
-   保留引用和元数据，方便审计生成结果。
-   对敏感场景清楚说明本地模型和私有部署模式。

### Required Review Checklist | 必要 Review 检查清单

Before merging security-relevant changes, reviewers should verify:

-   New external inputs have validation, authorization, and boundary checks.
-   File access is confined before `open()`, parser invocation, indexing, or LLM processing.
-   Tests cover the denied path as well as the successful path.
-   Documentation and `.env.example` describe any new security-sensitive setting.
-   The change has been checked with `ruff`, `pytest`, and relevant frontend build/tests.

合并安全相关改动前，reviewer 应确认：

-   新增外部输入具备验证、授权和边界检查。
-   文件访问在 `open()`、parser 调用、索引或 LLM 处理前已完成范围限制。
-   测试覆盖拒绝路径和成功路径。
-   文档和 `.env.example` 描述了新的安全敏感配置。
-   改动已通过 `ruff`、`pytest` 以及相关前端 build/tests。

---

## References | 参考

-   [**SPEC.md Section 7.2**](./SPEC.md) — Security Requirements and Controls (identity, data, application, operations, supply chain).
-   [**ARCHITECTURE.md**](./ARCHITECTURE.md) — System architecture with LangGraph design and security architecture section.
-   [**docs/05-deployment-runbook.md**](./docs/05-deployment-runbook.md) — Deployment, configuration, and network requirements.

-   [**SPEC.md 第 7.2 节**](./SPEC.md) — 安全需求与控制（身份、数据、应用、运维、供应链）。
-   [**ARCHITECTURE.md**](./ARCHITECTURE.md) — 系统架构，含 LangGraph 设计与安全架构章节。
-   [**docs/05-deployment-runbook.md**](./docs/05-deployment-runbook.md) — 部署、配置与网络需求。
