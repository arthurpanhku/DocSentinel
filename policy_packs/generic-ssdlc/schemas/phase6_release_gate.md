# Phase 6: Release Gate & Compliance Certificate

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase6_release_gate`
- phase: `6`
- phase_name: `Release Gate & Compliance Certificate`
- parent_agent: `release_gate_agent`
- schema_type: `fields`
- purpose: `Final security sign-off before production release. AI agent checks phase completeness, validates residual risk acceptance, and generates a compliance certificate referencing applicable frameworks.`

## Agent Guidance

- Aggregate pass/fail across all completed phases.
- Map residual risks to framework-specific risk acceptance criteria.
- Generate a Compliance Certificate referencing the project's selected compliance frameworks.
- For EU CRA: generate a vulnerability disclosure policy statement.
- For EU AI Act high-risk: check conformity assessment completeness.
- Flag controls with scheduled re-review dates for post-release monitoring.

## Framework Mappings

- NIST SSDF RV.3.3 — respond to vulnerability reports after release
- EU CRA Art. 14 — reporting vulnerability obligations
- EU AI Act Art. 43 — conformity assessment for high-risk AI
- ISO/IEC 27001:2022 §9.2 — internal audit and management review
- Japan METI AI Security §5 — responsible disclosure for AI systems

## Fields

### Field: residual_risks
- label: `Residual risks and open findings`
- required: `true`
- field_type: `textarea`
- group: `risk_acceptance`
- help_text: `List any security findings or controls that are not fully implemented at go-live. Each residual risk must include: description, severity, rationale for accepting, and planned remediation date.`

### Field: risk_acceptance_owner
- label: `Risk acceptance owner`
- required: `true`
- field_type: `text`
- group: `risk_acceptance`
- help_text: `Name and role of the business or security leader formally accepting residual risks.`

### Field: pentest_report_date
- label: `Most recent penetration test date`
- required: `false`
- field_type: `date`
- group: `assurance`
- help_text: `Date of the most recent penetration test or security assessment. Leave blank if not applicable.`

### Field: framework_attestations
- label: `Compliance framework attestations`
- required: `false`
- field_type: `multiselect`
- group: `compliance_attestation`
- help_text: `Select frameworks for which compliance is being attested in this release. The certificate will list these frameworks with the applicable controls assessed.`
- options:
  - `nist-ssdf`
  - `eu-cra`
  - `eu-ai-act`
  - `iso-27001-2022`
  - `iso-42001`
  - `owasp-samm`
  - `china-mlps2`
  - `singapore-mas-trm`

### Field: certificate_scope
- label: `Certificate scope description`
- required: `true`
- field_type: `textarea`
- group: `compliance_attestation`
- help_text: `Describe the scope of the release being certified: system name, version, deployment environment, and any explicitly excluded components.`

### Field: vulnerability_disclosure_policy
- label: `Vulnerability disclosure policy`
- required: `false`
- field_type: `textarea`
- group: `post_release`
- ask_when: `eu IN phase1_intake.geographic_scope OR phase1_intake.internet_facing == true`
- help_text: `Describe how security researchers and users can report vulnerabilities. Required by EU CRA Art. 14. Can reference a security.txt file or bug bounty program.`
- maps_to_frameworks: [`EU-CRA:Art.14`, `NIST-SSDF:RV.3`, `ISO29147`]

### Field: post_release_monitoring
- label: `Post-release security monitoring plan`
- required: `false`
- field_type: `textarea`
- group: `post_release`
- help_text: `Describe how the system will be monitored for security events and vulnerabilities after go-live, including alerting, review cadence, and escalation paths.`
- maps_to_frameworks: [`NIST-CSF:DE.AE`, `ISO27001:A.8.16`, `EU-AIAct:Art.12`]

### Field: next_review_date
- label: `Scheduled next security review date`
- required: `false`
- field_type: `date`
- group: `post_release`
- help_text: `When will the next scheduled security review or control re-assessment occur?`
