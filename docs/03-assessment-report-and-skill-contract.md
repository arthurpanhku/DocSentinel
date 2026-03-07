# 03 — Assessment Report and Skill Contract | 评估报告与 Skill 契约

|                 |                                            |
| :-------------- | :----------------------------------------- |
| **Status**      | [ ] Draft \| [ ] In Review \| [ ] Approved |
| **Version**     | 0.1                                        |
| **Related PRD** | Section 5.2.3 Skill, Section 6 Features    |

---

## 1. Assessment Report Schema | 评估报告结构

Agent outputs a **structured report** conforming to this schema. It is used for API responses, frontend rendering, and ServiceNow write-back.

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
    "status": { "type": "string", "enum": ["completed", "partial", "failed", "review_pending", "approved", "rejected", "escalated"] },
    "summary": { "type": "string", "description": "Executive summary of findings" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1, "description": "Overall confidence score" },
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
    "metadata": {
      "type": "object",
      "properties": {
        "scenario_id": { "type": "string" },
        "project_id": { "type": "string" },
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
  "required": ["format", "content", "metadata"],
  "properties": {
    "format": { "type": "string", "enum": ["markdown", "json"] },
    "content": {
      "oneOf": [
        { "type": "string" },
        { "type": "object", "description": "Structured content (e.g. spreadsheet rows)" }
      ]
    },
    "metadata": {
      "type": "object",
      "required": ["filename", "type"],
      "properties": {
        "filename": { "type": "string" },
        "type": { "type": "string", "description": "MIME type or extension" },
        "pages": { "type": "integer" },
        "language": { "type": "string" }
      }
    }
  }
}
```

---

## 3. Skill & Persona Definition | Skill 与角色定义

### 3.1 Skill Template Schema

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

### 3.2 Skill Execution Contract

-   **Input**: `parsed_documents` + `kb_chunks` + `history_chunks` + `skill_focus`
-   **Output**: Structured `AssessmentReport` fragment (JSON).

The Orchestrator injects the `system_prompt` and `risk_focus` into the LLM context to guide the generation.

---

## 4. Changelog | 修订记录

| Version | Date    | Changes                                                 |
| :------ | :------ | :------------------------------------------------------ |
| **0.1** | Initial | Draft Report Schema, Parser Output, and Skill Contract. |
