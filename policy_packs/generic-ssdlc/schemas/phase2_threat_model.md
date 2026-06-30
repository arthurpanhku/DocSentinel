# Phase 2: Threat Modeling & Security Requirements

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase2_threat_model`
- phase: `2`
- phase_name: `Threat Modeling & Security Requirements`
- parent_agent: `threat_model_agent`
- schema_type: `fields`
- purpose: `Collect architectural context to drive AI-assisted STRIDE threat analysis and generate a traceable Security Requirements Document (SRD) mapped to applicable frameworks.`

## Agent Guidance

- Accept architecture diagrams (image or description), OpenAPI specs, or free-text descriptions.
- Generate STRIDE threats from architecture input using the `generate_stride_threats` tool.
- For AI/ML systems, apply OWASP LLM Top 10 analysis using `generate_llm_security_threats`.
- Produce structured SRD with requirement IDs and framework citations.
- Surface supply chain threats if `third_party_dependencies` or `uses_open_source` were set in Phase 1.

## Framework Mappings

- NIST SSDF PW.1.1 — design software to meet security requirements
- NIST AI RMF MAP 1.1 — identify context and categorize risk for AI systems
- EU AI Act Art. 9 — risk management system for high-risk AI
- ISO/IEC 27034-1 §7.3 — application security controls
- OWASP SAMM Design Practice 2 — threat assessment
- OWASP LLM Top 10 — for AI/ML systems

## Fields

### Field: architecture_description
- label: `Architecture description`
- required: `true`
- field_type: `textarea`
- group: `architecture`
- help_text: `Describe the system architecture in plain text, or reference an uploaded diagram. Include: components, services, external integrations, and data stores.`

### Field: data_flows
- label: `Key data flows and trust boundaries`
- required: `true`
- field_type: `textarea`
- group: `architecture`
- help_text: `Describe how data moves between components, which boundaries require authentication, and where sensitive data is processed or stored.`

### Field: key_assets
- label: `Key assets to protect`
- required: `true`
- field_type: `textarea`
- group: `architecture`
- help_text: `List the most valuable assets: credentials, PII databases, model weights, API keys, financial records, etc.`

### Field: existing_controls
- label: `Security controls already in place`
- required: `false`
- field_type: `textarea`
- group: `architecture`
- help_text: `List any security controls already designed or implemented. The agent will avoid generating duplicate requirements.`

### Field: external_integrations
- label: `External APIs, services, or third-party integrations`
- required: `false`
- field_type: `textarea`
- group: `architecture`
- help_text: `e.g. payment gateways, identity providers, cloud AI APIs, data feeds.`

### Field: ai_model_inputs
- label: `AI model inputs and sources`
- required: `false`
- field_type: `textarea`
- group: `ai_threat_context`
- ask_when: `phase1_intake.involves_ai_ml == true`
- help_text: `Describe what data is fed into the AI model: user prompts, file uploads, structured data, real-time feeds. This drives prompt injection and data poisoning threat analysis.`
- maps_to_frameworks: [`OWASP-LLM:LLM01`, `OWASP-LLM:LLM06`, `EU-AIAct:Art.10`]

### Field: ai_model_outputs_used_by
- label: `How AI model outputs are used`
- required: `false`
- field_type: `textarea`
- group: `ai_threat_context`
- ask_when: `phase1_intake.involves_ai_ml == true`
- help_text: `Describe how model outputs are consumed: displayed to users, used in automated decisions, fed into other systems. Drives output monitoring and human oversight requirements.`
- maps_to_frameworks: [`EU-AIAct:Art.12`, `EU-AIAct:Art.14`, `NIST-AIRMF:MEASURE.2`]

### Field: sbom_file
- label: `Software Bill of Materials (SBOM)`
- required: `false`
- field_type: `file_upload`
- group: `supply_chain`
- help_text: `Upload a CycloneDX or SPDX SBOM file. The agent will identify known-vulnerable components and assess supply chain risk.`
- maps_to_frameworks: [`EU-CRA:Art.13(5)`, `NIST-SSDF:PW.4`, `SLSA:L2`]

### Field: target_srd_format
- label: `Preferred Security Requirements Document format`
- required: `false`
- field_type: `select`
- group: `output_preferences`
- options:
  - `stride_table`
  - `requirement_list`
  - `user_story_format`
  - `excel_export`
- help_text: `The agent will generate the SRD in the selected format.`
