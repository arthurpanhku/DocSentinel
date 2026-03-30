# 03 — Assessment Report and Skill Contract | 评估报告与 Skill 契约

|                 |                                            |
| :-------------- | :----------------------------------------- |
| **Status**      | [x] Updated (v4.0 aligned) \| [ ] In Review \| [ ] Approved |
| **Version**     | 0.3                                        |
| **Related PRD** | Section 5.2.3 Skill, Section 6 Features    |

---

## 1. Assessment Report Schema | 评估报告结构

Agent outputs a **structured report** conforming to this schema. It is used for API responses and optional ServiceNow write-back.

### 1.1 JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://security-ai-agent.example/schemas/assessment-report.json",
  "title": "AssessmentReport",
  "type": "object",
  "required": ["version", "task_id", "status", "summary"],
  "properties": {
    "version": { "type": "string", "const": "1.0" },
    "task_id": { "type": "string", "format": "uuid" },
    "status": { "type": "string", "enum": ["completed", "partial", "failed"] },
    "summary": { "type": "string", "description": "Executive summary of findings" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1, "description": "Overall confidence score (0.0–1.0)" },
    "risk_items": {
      "type": "array",
      "items": { "$ref": "#/$defs/RiskItem" }
    },
    "compliance_gaps": {
      "type": "array",
      "items": { "$ref": "#/$defs/ComplianceGap" }
    },
    "remediations": {
      "type": "array",
      "items": { "$ref": "#/$defs/Remediation" }
    },
    "sources": {
      "type": "array",
      "description": "Citation evidence from parsed documents",
      "items": { "$ref": "#/$defs/SourceCitation" }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "scenario_id": { "type": "string" },
        "project_id": { "type": "string" },
        "ssdlc_stage": { "type": "string", "enum": ["requirements", "design", "development", "testing", "deployment", "operations"], "description": "SSDLC stage this assessment covers" },
        "model_used": { "type": "string" },
        "completed_at": { "type": "string", "format": "date-time" }
      }
    },
    "format": { "type": "string", "enum": ["json", "markdown"], "default": "json" }
  },
  "$defs": {
    "RiskItem": {
      "type": "object",
      "required": ["id", "title", "severity"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "severity": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
        "description": { "type": "string" },
        "source_ref": { "type": "string", "description": "Reference to source doc/section" },
        "category": { "type": "string" }
      }
    },
    "ComplianceGap": {
      "type": "object",
      "required": ["id", "control_or_clause", "gap_description"],
      "properties": {
        "id": { "type": "string" },
        "control_or_clause": { "type": "string" },
        "gap_description": { "type": "string" },
        "evidence_suggestion": { "type": "string" },
        "framework": { "type": "string" }
      }
    },
    "Remediation": {
      "type": "object",
      "required": ["id", "action"],
      "properties": {
        "id": { "type": "string" },
        "action": { "type": "string" },
        "priority": { "type": "string", "enum": ["low", "medium", "high"] },
        "related_risk_ids": { "type": "array", "items": { "type": "string" } },
        "related_gap_ids": { "type": "array", "items": { "type": "string" } }
      }
    },
    "SourceCitation": {
      "type": "object",
      "required": ["id", "file", "excerpt"],
      "properties": {
        "id": { "type": "string" },
        "file": { "type": "string" },
        "page": { "type": "integer", "description": "Page number (if applicable)" },
        "paragraph_id": { "type": "string" },
        "excerpt": { "type": "string", "description": "Relevant excerpt from source" },
        "evidence_link": { "type": "string" },
        "score": { "type": "number", "description": "Relevance score" }
      }
    }
  }
}
```

*Save this as `docs/schemas/assessment-report.json` for validation.*

### 1.2 Markdown Template (Optional)

When `format == "markdown"`, the output should follow:

```markdown
# Assessment Report | 安全评估报告
**Task ID**: {task_id}  
**Completed**: {completed_at}

## Summary | 摘要
{summary}

## Risk Items | 风险项
| ID  | Title | Severity | Description |
| --- | ----- | -------- | ----------- |
| ... | ...   | ...      | ...         |

## Compliance Gaps | 合规差距
| Control/Clause | Gap Description | Evidence Suggestion |
| -------------- | --------------- | ------------------- |
| ...            | ...             | ...                 |

## Remediations | 整改建议
| Priority | Action | Related Risks/Gaps |
| -------- | ------ | ------------------ |
| ...      | ...    | ...                |
```

---

## 2. Parser Output Schema | 文件解析输出结构

Unified output format for both Assessment Input and Knowledge Base Ingestion.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ParsedDocument",
  "type": "object",
  "required": ["metadata", "content"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["filename", "type"],
      "properties": {
        "filename": { "type": "string" },
        "type": { "type": "string", "enum": ["pdf", "docx", "xlsx", "pptx", "txt", "md"] },
        "parser_engine": { "type": "string", "enum": ["docling", "legacy"], "default": "legacy" },
        "upload_time": { "type": "string", "format": "date-time" },
        "scenario_id": { "type": "string", "description": "Optional scenario context" },
        "file_hash": { "type": "string", "description": "SHA hash for deduplication" }
      }
    },
    "content": { "type": "string", "description": "Markdown or plain-text content" },
    "raw_structure": {
      "type": "object",
      "description": "Optional structured JSON for spreadsheets/tables (null for text formats)"
    },
    "chunk_ids": {
      "type": "array",
      "items": { "type": "string" },
      "description": "IDs of chunks created when document is ingested into the KB"
    }
  }
}
```

---

## 3. Task Lifecycle Models | 任务生命周期模型

When `POST /assessments` is called, the API returns an `AssessmentTaskCreated` immediately (non-blocking). The task progresses through statuses tracked by `AssessmentTaskResult`.

### 3.1 AssessmentTaskCreated (returned on submission)

| Field      | Type   | Description                  |
| :--------- | :----- | :--------------------------- |
| `task_id`  | UUID   | Unique task identifier       |
| `status`   | string | `"accepted"` or `"queued"`   |
| `message`  | string | Optional informational text  |

### 3.2 AssessmentTaskResult (returned on polling)

| Field            | Type               | Description                                                                                         |
| :--------------- | :----------------- | :-------------------------------------------------------------------------------------------------- |
| `task_id`        | UUID               | Unique task identifier                                                                              |
| `status`         | string             | `pending` → `running` → `completed` / `failed` / `review_pending` / `approved` / `rejected` / `escalated` |
| `report`         | AssessmentReport   | Present when `status == "completed"`                                                                |
| `error_message`  | string             | Present when `status == "failed"`                                                                   |
| `created_at`     | datetime           | Task creation time (UTC)                                                                            |
| `completed_at`   | datetime           | Task completion time (UTC)                                                                          |
| `version`        | int                | Report version (incremented on revisions)                                                           |
| `assignee`       | string             | Optional human assignee for review                                                                  |
| `comments`       | array              | Review comments (for human-in-the-loop workflow)                                                    |

---

## 4. Skill & Persona Definition | Skill 与角色定义

### 4.1 Skill Template Schema

Each skill (or persona) is defined by a JSON template.

```json
{
  "id": "iso-27001-auditor",
  "name": "ISO 27001 Lead Auditor",
  "description": "Formal ISMS audit focusing on process, documentation, and controls.",
  "system_prompt": "You are an ISO 27001 Lead Auditor...",
  "risk_focus": ["Access Control", "Supplier Security"],
  "compliance_frameworks": ["ISO/IEC 27001:2013"],
  "is_builtin": true
}
```

### 4.2 SSDLC Stage Skills (Built-in)

Each SSDLC stage has a dedicated built-in skill:

| Stage | Skill ID | Risk Focus | Example Frameworks |
| :---- | :------- | :--------- | :----------------- |
| **Requirements** | `ssdlc-requirements` | Security requirements completeness, compliance mapping, risk analysis | GDPR, ISO 27001, NIST |
| **Design** | `ssdlc-design` | Architecture security, threat modeling (STRIDE/DREAD), encryption/permission design | OWASP, NIST SP 800-53, CIS |
| **Development** | `ssdlc-development` | Secure coding standards, anti-injection, XSS prevention, input validation | OWASP Top 10, CWE, CERT |
| **Testing** | `ssdlc-testing` | SAST/DAST findings triage, penetration test evaluation, vulnerability verification | OWASP ASVS, PCI DSS |
| **Deployment** | `ssdlc-deployment` | Release readiness, config security, key management, hardening | CIS Benchmarks, DISA STIG |
| **Operations** | `ssdlc-operations` | Vulnerability monitoring, incident response, patch management, log audit | NIST CSF, SOC2, ISO 27001 |

### 4.3 Skill Execution Contract

-   **Input**: `parsed_documents` + `kb_chunks` + `history_chunks` + `skill_focus` + `ssdlc_stage` (optional)
-   **Output**: Structured `AssessmentReport` fragment (JSON).

The LangGraph orchestrator injects the `system_prompt`, `risk_focus`, `ssdlc_stage`, and stage-specific checklist into the LLM context to guide the generation.

---

## 5. Changelog | 修订记录

| Version | Date    | Changes                                                 |
| :------ | :------ | :------------------------------------------------------ |
| **0.3** | 2026-03 | Added SSDLC stage skills (6 stages), `ssdlc_stage` field in report metadata, LangGraph execution contract. |
| **0.2** | 2026-03 | Aligned ParsedDocument with code (removed `format`, added `parser_engine`, `raw_structure`, `chunk_ids`). Added `SourceCitation` and `sources` to report schema. Added Task Lifecycle Models section. Fixed `AssessmentReport.status` enum to match code. |
| **0.1** | Initial | Draft Report Schema, Parser Output, and Skill Contract. |
