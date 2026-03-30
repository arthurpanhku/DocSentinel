# Security Policy | 安全策略

This document covers vulnerability disclosure and security-related practices for the **DocSentinel** project. It aligns with [**PRD §7.2 Security Requirements and Controls**](./SPEC.md).

本文档涵盖 **DocSentinel** 项目的漏洞披露与安全实践，遵循 [**PRD §7.2 安全需求与控制**](./SPEC.md)。

---

## Supported Versions | 支持版本

| Version   | Supported          |
| :-------- | :----------------- |
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
-   **Prompt Injection Guardrails**: Input sanitization via regex pattern detection and length limits is enforced before content reaches the LLM (see `app/core/guardrails.py`). Malicious inputs are rejected with HTTP 400.
-   **TLS**: In production, use HTTPS and TLS 1.2+ for all endpoints and external calls ([PRD §7.2 DATA-01](./SPEC.md)).
-   **Auth**: API currently does not enforce authentication in the MVP; add AAD/API Key as per [PRD §5.2.8 and §7.2 IAM](./SPEC.md) before exposing externally.

-   **机密信息**：请勿提交 `.env` 或任何包含 `SECRET_KEY`、API Key、密码的文件。`.env.example` 仅作为模板使用。
-   **输入验证**：强制执行文件类型与大小限制（见 `UPLOAD_MAX_FILE_SIZE_MB`、`UPLOAD_MAX_FILES`）。仅解析允许的扩展名（见 `app/parser/service.py`）。
-   **提示注入防护**：通过正则模式检测和长度限制对输入进行清洗，在内容到达 LLM 之前执行（见 `app/core/guardrails.py`）。恶意输入将被 HTTP 400 拒绝。
-   **TLS**：生产环境中，所有端点与外部调用必须使用 HTTPS 和 TLS 1.2+（[PRD §7.2 DATA-01](./SPEC.md)）。
-   **认证**：MVP 阶段 API 暂未强制认证；在对外暴露前，请根据 [PRD §5.2.8 与 §7.2 IAM](./SPEC.md) 添加 AAD/API Key 认证。

---

## References | 参考

-   [**SPEC.md Section 7.2**](./SPEC.md) — Security Requirements and Controls (identity, data, application, operations, supply chain).
-   [**docs/05-deployment-runbook.md**](./docs/05-deployment-runbook.md) — Deployment, configuration, and network requirements.

-   [**SPEC.md 第 7.2 节**](./SPEC.md) — 安全需求与控制（身份、数据、应用、运维、供应链）。
-   [**docs/05-deployment-runbook.md**](./docs/05-deployment-runbook.md) — 部署、配置与网络需求。
