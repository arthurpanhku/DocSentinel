# 03 — Assessment Report and Skill Contract | 评估报告与 Skill 契约

|                 |                                              |
| :-------------- | :------------------------------------------- |
| **Status**      | [x] Updated (v4.0 aligned, v2.0) \| [ ] In Review \| [ ] Approved |
| **Version**     | 2.0                                          |
| **Related PRD** | Section 3.2 SSDLC Phases, Section 6 Features |

---

## 1. Assessment Report Schema | 评估报告结构

Agent outputs a **structured report** conforming to this schema. It is used for API responses, cross-phase traceability, sign-off workflows, and optional ServiceNow write-back. Each report is tagged with the SSDLC phase that generated it.

### 1.1 JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://docsentinel.example/schemas/assessment-report.json",
  "title": "SSDLCAssessmentReport",
  "type": "object",
  "required": ["version", "task_id", "phase", "status", "summary"],
  "properties": {
    "version": { "type": "string", "const": "2.0" },
    "task_id": { "type": "string", "format": "uuid" },
    "phase": {
      "type": "string",
      "enum": ["requirements", "design", "development", "testing", "deployment", "operations", "full_ssdlc"],
      "description": "SSDLC phase that produced this report"
    },
    "status": {
      "type": "string",
      "enum": ["completed", "partial", "failed", "review_pending", "approved", "rejected", "escalated"]
    },
    "summary": { "type": "string", "description": "Executive summary of findings for this phase" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1, "description": "Overall confidence score (0.0–1.0)" },
    "risk_items": {
      "type": "array",
      "items": { "$ref": "#/$defs/RiskItem" }
    },
    "compliance_gaps": {
      "type": "array",
      "items": { "$ref": "#/$defs/ComplianceGap" }
    },
    "threat_model": {
      "type": "object",
      "description": "STRIDE/DREAD threat model (primarily from Design phase)",
      "$ref": "#/$defs/ThreatModel"
    },
    "vulnerabilities": {
      "type": "array",
      "description": "Parsed SAST/DAST/Pentest findings (primarily from Testing phase)",
      "items": { "$ref": "#/$defs/Vulnerability" }
    },
    "remediations": {
      "type": "array",
      "items": { "$ref": "#/$defs/Remediation" }
    },
    "cross_phase_refs": {
      "type": "array",
      "description": "References linking findings across SSDLC phases",
      "items": { "$ref": "#/$defs/CrossPhaseRef" }
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
        "completed_at": { "type": "string", "format": "date-time" },
        "ssdlc_phase": { "type": "string" },
        "skill_id": { "type": "string" }
      }
    },
    "format": { "type": "string", "enum": ["json", "markdown"], "default": "json" }
  },
  "$defs": {
    "RiskItem": {
      "type": "object",
      "required": ["id", "title", "severity", "phase"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "severity": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
        "description": { "type": "string" },
        "source_ref": { "type": "string", "description": "Reference to source doc/section" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1, "description": "Finding-level confidence score (0.0–1.0)" },
        "citation_ids": { "type": "array", "items": { "type": "string" }, "description": "IDs referencing entries in top-level sources[]" },
        "category": { "type": "string" },
        "phase": { "type": "string", "description": "SSDLC phase where this risk was identified" }
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
        "confidence": { "type": "number", "minimum": 0, "maximum": 1, "description": "Gap-level confidence score (0.0–1.0)" },
        "citation_ids": { "type": "array", "items": { "type": "string" }, "description": "IDs referencing entries in top-level sources[]" },
        "framework": { "type": "string" },
        "phase": { "type": "string" }
      }
    },
    "ThreatModel": {
      "type": "object",
      "properties": {
        "methodology": { "type": "string", "enum": ["STRIDE", "DREAD", "STRIDE_DREAD"] },
        "threats": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "category", "description"],
            "properties": {
              "id": { "type": "string" },
              "category": { "type": "string", "enum": ["Spoofing", "Tampering", "Repudiation", "InformationDisclosure", "DenialOfService", "ElevationOfPrivilege"] },
              "description": { "type": "string" },
              "affected_component": { "type": "string" },
              "dread_score": {
                "type": "object",
                "properties": {
                  "damage": { "type": "integer", "minimum": 1, "maximum": 10 },
                  "reproducibility": { "type": "integer", "minimum": 1, "maximum": 10 },
                  "exploitability": { "type": "integer", "minimum": 1, "maximum": 10 },
                  "affected_users": { "type": "integer", "minimum": 1, "maximum": 10 },
                  "discoverability": { "type": "integer", "minimum": 1, "maximum": 10 },
                  "total": { "type": "number" }
                }
              },
              "mitigations": { "type": "array", "items": { "type": "string" } }
            }
          }
        }
      }
    },
    "Vulnerability": {
      "type": "object",
      "required": ["id", "title", "severity", "source_tool"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "severity": { "type": "string", "enum": ["info", "low", "medium", "high", "critical"] },
        "source_tool": { "type": "string", "description": "SAST/DAST tool that found this (e.g. SonarQube, Burp)" },
        "cwe_id": { "type": "string" },
        "cvss_score": { "type": "number" },
        "location": { "type": "string", "description": "File path, URL, or component" },
        "description": { "type": "string" },
        "remediation": { "type": "string" },
        "status": { "type": "string", "enum": ["open", "in_progress", "fixed", "accepted", "false_positive"] },
        "linked_threat_id": { "type": "string", "description": "Cross-ref to threat model threat ID" }
      }
    },
    "Remediation": {
      "type": "object",
      "required": ["id", "action"],
      "properties": {
        "id": { "type": "string" },
        "action": { "type": "string" },
        "priority": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
        "phase": { "type": "string", "description": "SSDLC phase this remediation applies to" },
        "related_risk_ids": { "type": "array", "items": { "type": "string" } },
        "related_gap_ids": { "type": "array", "items": { "type": "string" } },
        "related_vuln_ids": { "type": "array", "items": { "type": "string" } },
        "related_threat_ids": { "type": "array", "items": { "type": "string" } },
        "external_ticket": { "type": "string", "description": "Optional external tracking reference (e.g. Jira key or GitHub Issue URL)" }
      }
    },
    "CrossPhaseRef": {
      "type": "object",
      "required": ["source_phase", "source_id", "target_phase", "target_id"],
      "properties": {
        "source_phase": { "type": "string" },
        "source_id": { "type": "string" },
        "target_phase": { "type": "string" },
        "target_id": { "type": "string" },
        "relationship": { "type": "string", "description": "e.g. 'threat_to_test', 'risk_to_remediation'" }
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
# SSDLC Assessment Report | 安全评估报告
**Task ID**: {task_id}
**Phase**: {phase}
**Completed**: {completed_at}

## Summary | 摘要
{summary}

## Risk Items | 风险项
| ID  | Title | Severity | Phase | Confidence | Description | Citations |
| --- | ----- | -------- | ----- | ---------- | ----------- | --------- |
| ... | ...   | ...      | ...   | ...        | ...         | ...       |

## Threat Model | 威胁建模 (Design Phase)
### Methodology: {methodology}
| ID  | Category | Description | Affected Component | DREAD Score |
| --- | -------- | ----------- | ------------------ | ----------- |
| ... | ...      | ...         | ...                | ...         |

## Vulnerabilities | 漏洞 (Testing Phase)
| ID  | Title | Severity | Source Tool | CWE | Location | Status |
| --- | ----- | -------- | ----------- | --- | -------- | ------ |
| ... | ...   | ...      | ...         | ... | ...      | ...    |

## Compliance Gaps | 合规差距
| Control/Clause | Gap Description | Framework | Phase | Confidence | Evidence Suggestion | Citations |
| -------------- | --------------- | --------- | ----- | ---------- | ------------------- | --------- |
| ...            | ...             | ...       | ...   | ...        | ...                 | ...       |

## Remediations | 整改建议
| Priority | Action | Phase | Related Risks/Threats/Vulns |
| -------- | ------ | ----- | --------------------------- |
| ...      | ...    | ...   | ...                         |

## Cross-Phase Traceability | 跨阶段追溯
| Source Phase | Source ID | Target Phase | Target ID | Relationship |
| ----------- | --------- | ------------ | --------- | ------------ |
| ...         | ...       | ...          | ...       | ...          |
```

---

## 2. Parser Output Schema | 文件解析输出结构

Unified output format for both assessment input and knowledge base ingestion. Extended to support SAST/DAST report formats.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ParsedDocument",
  "type": "object",
  "required": ["metadata", "content"],
  "properties": {
    "format": { "type": "string", "enum": ["markdown", "json", "sarif"] },
    "metadata": {
      "type": "object",
      "required": ["filename", "type"],
      "properties": {
        "filename": { "type": "string" },
        "type": { "type": "string", "description": "MIME type or extension (pdf, docx, xlsx, pptx, txt, md, mmd, mermaid, sarif, etc.)" },
        "parser_engine": { "type": "string", "enum": ["docling", "legacy"], "default": "legacy" },
        "pages": { "type": "integer" },
        "language": { "type": "string" },
        "upload_time": { "type": "string", "format": "date-time" },
        "scenario_id": { "type": "string", "description": "Optional scenario context" },
        "file_hash": { "type": "string", "description": "SHA hash for deduplication" },
        "source_tool": { "type": "string", "description": "For SAST/DAST reports: tool name" },
        "ssdlc_phase_hint": { "type": "string", "description": "Suggested SSDLC phase for this document" }
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

Each skill (or persona) is defined by a JSON template. Skills are now organized by SSDLC phase.

```json
{
  "id": "design-threat-modeler",
  "name": "Threat Modeler",
  "description": "Performs STRIDE/DREAD threat modeling on architecture and design documents.",
  "ssdlc_phase": "design",
  "system_prompt": "You are a security threat modeling expert. Analyze the provided architecture document using the STRIDE methodology...",
  "risk_focus": ["Spoofing", "Tampering", "Information Disclosure", "Elevation of Privilege"],
  "compliance_frameworks": ["OWASP", "NIST SP 800-53"],
  "tools": ["stride_analyzer", "dread_scorer"],
  "is_builtin": true
}
```

### 4.2 Built-in Skills by SSDLC Phase

| SSDLC Phase | Skill ID | Name | Focus |
| :--- | :--- | :--- | :--- |
| **Requirements** | `req-compliance-analyst` | Compliance Analyst | GDPR, PCI DSS, SOC2, ISO 27001 compliance mapping |
| **Requirements** | `req-risk-assessor` | Risk Assessor | Project risk classification, data sensitivity analysis |
| **Design** | `design-threat-modeler` | Threat Modeler | STRIDE/DREAD analysis, attack surface mapping |
| **Design** | `design-security-architect` | Security Architect | Architecture patterns, encryption, IAM design review |
| **Development** | `dev-secure-code-reviewer` | Secure Code Reviewer | OWASP Secure Coding Practices, language-specific guidance |
| **Development** | `dev-sast-analyst` | SAST Analyst | SAST findings triage, false positive reduction |
| **Testing** | `test-pentest-analyst` | Pentest Analyst | Penetration test report analysis, finding prioritization |
| **Testing** | `test-vuln-manager` | Vulnerability Manager | SAST/DAST triage, remediation tracking |
| **Deployment** | `deploy-release-reviewer` | Release Security Reviewer | Pre-release checklist, configuration audit |
| **Deployment** | `deploy-hardening-specialist` | Hardening Specialist | CIS benchmarks, container/server hardening |
| **Operations** | `ops-vuln-monitor` | Vulnerability Monitor | CVE analysis, patch priority assessment |
| **Operations** | `ops-incident-responder` | Incident Responder | Incident analysis, response recommendations |

### 4.3 SSDLC Stage Skills (Built-in)

Each SSDLC stage has a dedicated built-in skill:

| Stage | Skill ID | Risk Focus | Example Frameworks |
| :---- | :------- | :--------- | :----------------- |
| **Requirements** | `ssdlc-requirements` | Security requirements completeness, compliance mapping, risk analysis | GDPR, ISO 27001, NIST |
| **Design** | `ssdlc-design` | Architecture security, threat modeling (STRIDE/DREAD), encryption/permission design | OWASP, NIST SP 800-53, CIS |
| **Development** | `ssdlc-development` | Secure coding standards, anti-injection, XSS prevention, input validation | OWASP Top 10, CWE, CERT |
| **Testing** | `ssdlc-testing` | SAST/DAST findings triage, penetration test evaluation, vulnerability verification | OWASP ASVS, PCI DSS |
| **Deployment** | `ssdlc-deployment` | Release readiness, config security, key management, hardening | CIS Benchmarks, DISA STIG |
| **Operations** | `ssdlc-operations` | Vulnerability monitoring, incident response, patch management, log audit | NIST CSF, SOC2, ISO 27001 |

### 4.4 Skill Execution Contract

-   **Input**: `parsed_documents` + `kb_chunks` (phase-specific collection) + `history_chunks` + `skill_focus` + `ssdlc_stage` (optional) + `ssdlc_state` (cross-phase context from LangGraph)
-   **Output**: Structured `SSDLCAssessmentReport` fragment (JSON) with phase tag and cross-phase references.

The LangGraph orchestrator injects the `system_prompt`, `risk_focus`, `tools`, `ssdlc_stage`, stage-specific checklist, and cross-phase state into the LLM context to guide the generation.

---

## 5. Changelog | 修订记录

| Version | Date    | Changes                                                 |
| :------ | :------ | :------------------------------------------------------ |
| **2.0** | 2026-03 | Major rewrite: SSDLC phase-tagged reports, ThreatModel schema, Vulnerability schema, CrossPhaseRef, SourceCitation, phase-specific skills, SARIF parser support, SSDLC stage skills (6 stages), `ssdlc_stage` field in report metadata, LangGraph execution contract. |
| **0.1** | Initial | Draft Report Schema, Parser Output, and Skill Contract. |
