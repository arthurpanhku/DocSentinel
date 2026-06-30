# Phase 4: Build Security & SAST/SCA

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase4_build_security`
- phase: `4`
- phase_name: `Build Security & SAST/SCA`
- parent_agent: `build_security_agent`
- schema_type: `fields`
- purpose: `Collect and analyze build-time security artifacts: SAST findings, dependency scans, SBOMs, container image scans, and CI/CD pipeline integrity. Assess SLSA build level and model provenance for AI systems.`

## Agent Guidance

- Parse uploaded SARIF files using `analyze_sarif` tool — triage findings by severity and false-positive likelihood.
- Parse CycloneDX/SPDX SBOMs using `analyze_sbom` tool — flag known-vulnerable components against CVE feeds.
- Assess SLSA level using `assess_slsa_level` tool based on pipeline description.
- For AI/ML systems, check model card completeness and training data source attestation.
- Generate a Build Security Report with pass/fail per control.

## Framework Mappings

- NIST SSDF PW.4.4 — use third-party reviewed software
- NIST SSDF PW.7.2 — test to verify security requirements
- EU CRA Annex I §1(e) — vulnerability handling policy
- EU CRA Art. 13(5) — SBOM generation and maintenance
- SLSA L1–L4 — supply chain levels for software artifacts
- CIS Controls v8 #16 — application software security
- OWASP SAMM Implementation Practice 2 — secure build and deployment

## Fields

### Field: sast_report_file
- label: `SAST scan results (SARIF format)`
- required: `false`
- field_type: `file_upload`
- group: `code_analysis`
- help_text: `Upload SARIF JSON output from any SAST tool (Semgrep, CodeQL, Checkmarx, Veracode, etc.). The agent will triage findings and generate a prioritized remediation plan.`
- maps_to_frameworks: [`NIST-SSDF:PW.7`, `OWASP-SAMM:I-SR`, `CIS-v8:#16`]

### Field: sca_sbom_file
- label: `SBOM or SCA report (CycloneDX / SPDX / CSV)`
- required: `false`
- field_type: `file_upload`
- group: `dependency_analysis`
- help_text: `Upload a CycloneDX JSON/XML, SPDX, or SCA CSV export. The agent will identify known-vulnerable components and assess EU CRA SBOM requirements.`
- maps_to_frameworks: [`EU-CRA:Art.13(5)`, `NIST-SSDF:PW.4`, `SLSA:L2`]

### Field: container_scan_file
- label: `Container image scan results`
- required: `false`
- field_type: `file_upload`
- group: `dependency_analysis`
- help_text: `Upload Trivy, Grype, or Snyk container scan output (JSON or text). Applicable for containerized applications.`
- maps_to_frameworks: [`CIS-Docker`, `NIST-SSDF:PW.4`]

### Field: pipeline_description
- label: `CI/CD pipeline description`
- required: `true`
- field_type: `textarea`
- group: `build_integrity`
- help_text: `Describe your build pipeline: build system used, whether builds are hermetic, whether artifacts are signed, provenance attestations generated, and access controls on pipeline configuration.`
- maps_to_frameworks: [`SLSA:L1-L4`, `NIST-SSDF:PW.4`, `EU-CRA:Annex-I`]

### Field: secrets_scan_result
- label: `Secrets / credential scan result`
- required: `false`
- field_type: `select`
- group: `code_analysis`
- options:
  - `passed_no_findings`
  - `passed_false_positives_triaged`
  - `findings_remediated`
  - `not_run`
- help_text: `Result of running a secrets detection tool (truffleHog, GitLeaks, detect-secrets).`
- maps_to_frameworks: [`OWASP-ASVS:V2.10`, `CIS-v8:#3`]

### Field: model_card_file
- label: `AI model card or documentation`
- required: `false`
- field_type: `file_upload`
- group: `ai_provenance`
- ask_when: `phase1_intake.involves_ai_ml == true`
- help_text: `Upload model card, factsheet, or equivalent documentation covering intended use, performance metrics, limitations, and training data sources.`
- maps_to_frameworks: [`ISO-42001:§7.5`, `EU-AIAct:Art.11`, `NIST-AIRMF:GOVERN.4`]

### Field: model_provenance
- label: `AI model provenance and supply chain`
- required: `false`
- field_type: `textarea`
- group: `ai_provenance`
- ask_when: `phase1_intake.involves_ai_ml == true`
- help_text: `Describe where the model comes from (trained in-house, fine-tuned from a foundation model, API call to third-party model). Include version, source, and license.`
- maps_to_frameworks: [`NIST-AIRMF:MAP.2`, `ISO-42001:§8.4`]
