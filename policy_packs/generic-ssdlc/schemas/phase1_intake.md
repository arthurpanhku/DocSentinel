# Phase 1: Intake & Classification

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase1_intake`
- phase: `1`
- phase_name: `Intake & Classification`
- parent_agent: `intake_agent`
- schema_type: `fields`
- purpose: `Collect project context to determine applicable compliance frameworks, AI system risk class, and which SSDLC phases and controls apply.`

## Agent Guidance

- Accept free-text project descriptions and extract structured fields from natural language where confidence is high.
- If `involves_ai_ml` is true and `geographic_scope` includes `eu`, prompt for `ai_eu_risk_class` using EU AI Act Art. 6–7 criteria.
- Use `geographic_scope` and `data_classification` to recommend applicable compliance frameworks.
- Do not ask for evidence here; evidence belongs in Phase 5 (Control Verification).

## Framework Mappings

- NIST SSDF PS.1.1 — document security requirements for all projects
- NIST AI RMF GOVERN 1.1 — governance for AI/ML involvement
- EU AI Act Art. 6–7 — risk classification for AI systems in EU market
- EU CRA Art. 13 — due diligence for products with digital elements in EU market
- ISO/IEC 42001 §4.1–4.3 — context of the organization for AI management systems
- China MLPS 2.0 §4.1 — protection class determination for CN-scoped systems
- Singapore MAS TRM §3 — risk categorization for SG financial institutions
- OWASP SAMM Governance Practice 1 — all projects

## Fields

### Field: project_name
- label: `Project or product name`
- required: `true`
- field_type: `text`
- group: `business_context`
- help_text: `The canonical name used to identify this application, service, or product release.`

### Field: business_owner
- label: `Business owner`
- required: `true`
- field_type: `text`
- group: `business_context`
- help_text: `Person or team accountable for the business outcome of this project.`

### Field: product_manager
- label: `Product manager / technical lead`
- required: `false`
- field_type: `text`
- group: `business_context`

### Field: release_type
- label: `Release type`
- required: `true`
- field_type: `select`
- group: `business_context`
- options:
  - `new_product`
  - `major_release`
  - `minor_release`
  - `patch`
  - `ai_model_update`
- help_text: `New product and major releases trigger the full SSDLC phase set. Minor releases and patches may use an express path.`
- maps_to_frameworks: [`NIST-SSDF:PS.1.1`]

### Field: system_type
- label: `System type (select all that apply)`
- required: `true`
- field_type: `multiselect`
- group: `system_profile`
- options:
  - `web_app`
  - `api_service`
  - `mobile_app`
  - `genai_system`
  - `ml_model`
  - `iot_device`
  - `rpa_bot`
  - `data_pipeline`
  - `saas_product`
  - `other`
- help_text: `Select all that apply. Selecting genai_system or ml_model activates AI-specific controls and EU AI Act classification.`
- maps_to_frameworks: [`EU-AIAct:Art.6`, `NIST-AIRMF:GOVERN.1.1`]

### Field: hosting_model
- label: `Hosting / runtime model`
- required: `true`
- field_type: `select`
- group: `system_profile`
- options:
  - `cloud_aws`
  - `cloud_azure`
  - `cloud_gcp`
  - `cloud_other`
  - `on_premise`
  - `hybrid`
  - `saas_vendor`
  - `customer_hosted`
- maps_to_frameworks: [`ISO27001:A.8.1`, `CIS-v8:#1`]
- maps_to_controls: [`GEN-ENC-02`, `GEN-BCP-01`, `GEN-IAM-03`]

### Field: internet_facing
- label: `Internet-facing (accessible from public internet)`
- required: `true`
- field_type: `boolean`
- group: `exposure`
- maps_to_frameworks: [`NIST-SSDF:PW.1`, `EU-CRA:Art.13`]
- maps_to_controls: [`GEN-IAM-01`, `GEN-ENC-01`, `GEN-VUL-02`, `GEN-LOG-01`, `GEN-SEC-02`]

### Field: data_classification
- label: `Data types handled (select all that apply)`
- required: `true`
- field_type: `multiselect`
- group: `data_profile`
- options:
  - `public`
  - `internal`
  - `confidential`
  - `restricted`
  - `pii`
  - `financial`
  - `health`
  - `national_security`
- help_text: `Select the highest sensitivity level handled. PII triggers GDPR/PIPL controls. Health and financial data activate sector-specific overlays.`
- maps_to_frameworks: [`GDPR:Art.4`, `PIPL:Art.4`, `HIPAA:§164.304`]
- maps_to_controls: [`GEN-PRV-01`, `GEN-PRV-02`, `GEN-ENC-02`]

### Field: geographic_scope
- label: `Geographic scope of users / data subjects`
- required: `true`
- field_type: `multiselect`
- group: `compliance_scope`
- options:
  - `us`
  - `eu`
  - `cn`
  - `sg`
  - `jp`
  - `au`
  - `global`
  - `other`
- help_text: `Determines which regulatory frameworks apply. EU scope activates GDPR and optionally EU CRA / EU AI Act. CN scope activates MLPS 2.0 and PIPL.`
- maps_to_frameworks: [`GDPR:Art.3`, `PIPL:Art.3`, `EU-CRA:Art.2`, `MLPS2:§4.1`]
- maps_to_controls: [`CRA-VUL-01`, `CRA-SBOM-01`, `EUAI-TR-01`, `MLPS2-IAM-01`, `MLPS2-LOG-01`, `MAS-IAM-01`, `MAS-LOG-01`]

### Field: involves_ai_ml
- label: `Does this project involve AI or machine learning?`
- required: `true`
- field_type: `boolean`
- group: `ai_profile`
- help_text: `Answer yes if the project uses, trains, fine-tunes, or embeds any AI/ML model, LLM, generative AI, computer vision, or recommendation system.`
- maps_to_controls: [`AI-SEC-01`, `AI-SEC-02`, `AI-SEC-03`, `AI-SEC-05`, `AI-SEC-06`, `AI-GOV-01`]

### Field: ai_system_type
- label: `AI system type`
- required: `false`
- field_type: `select`
- group: `ai_profile`
- ask_when: `involves_ai_ml == true`
- options:
  - `llm_genai`
  - `classical_ml`
  - `cv_system`
  - `nlp_pipeline`
  - `recommendation`
  - `agentic_system`
  - `other`
- maps_to_frameworks: [`EU-AIAct:Art.3`, `NIST-AIRMF:GOVERN.1`]

### Field: ai_eu_risk_class
- label: `EU AI Act risk classification`
- required: `false`
- field_type: `select`
- group: `ai_profile`
- ask_when: `involves_ai_ml == true AND eu IN geographic_scope`
- options:
  - `unacceptable`
  - `high`
  - `limited`
  - `minimal`
- help_text: `Refer to EU AI Act Art. 6–7 and Annexes III–IV. High-risk AI systems require conformity assessment and quality management system (Art. 9, 17, 43).`
- maps_to_frameworks: [`EU-AIAct:Art.6`, `EU-AIAct:Art.7`, `EU-AIAct:Annex-III`]
- maps_to_controls: [`AI-SEC-04`, `AI-SEC-07`, `AI-GOV-02`, `AI-GOV-03`]

### Field: ai_act_annex_iii_category
- label: `EU AI Act Annex III category`
- required: `false`
- field_type: `select`
- group: `ai_profile`
- ask_when: `involves_ai_ml == true AND ai_eu_risk_class == high AND eu IN geographic_scope`
- options:
  - `biometrics`
  - `critical_infrastructure`
  - `education_vocational_training`
  - `employment_worker_management`
  - `essential_private_public_services`
  - `law_enforcement`
  - `migration_asylum_border_control`
  - `administration_of_justice_democratic_processes`
  - `not_applicable`
- help_text: `Identifies whether the AI system falls under an Annex III high-risk use case.`
- maps_to_frameworks: [`EU-AIAct:Annex-III`, `EU-AIAct:Art.6`]
- maps_to_controls: [`AI-GOV-02`, `AI-GOV-03`, `EUAI-CA-01`]

### Field: ai_training_data_source
- label: `AI training / fine-tuning data source`
- required: `false`
- field_type: `multiselect`
- group: `ai_profile`
- ask_when: `involves_ai_ml == true`
- options:
  - `public_datasets`
  - `organization_sensitive_data`
  - `user_generated`
  - `scraped_web`
  - `licensed_data`
  - `synthetic`
  - `not_applicable`
- maps_to_frameworks: [`EU-AIAct:Art.10`, `ISO-42001:§8.4`]

### Field: ai_model_provider
- label: `AI model or API provider (if using third-party model)`
- required: `false`
- field_type: `text`
- group: `ai_profile`
- ask_when: `involves_ai_ml == true`
- help_text: `e.g. OpenAI, Anthropic, Google Vertex AI, AWS Bedrock, Hugging Face, or internal.`

### Field: third_party_dependencies
- label: `Third-party software components, SDKs, or vendor APIs involved`
- required: `true`
- field_type: `boolean`
- group: `supply_chain`
- maps_to_frameworks: [`NIST-SSDF:PW.4`, `EU-CRA:Art.13`, `ISO27001:A.5.19`]
- maps_to_controls: [`GEN-TPR-01`, `GEN-SC-01`]

### Field: uses_open_source
- label: `Open-source software or libraries included`
- required: `true`
- field_type: `boolean`
- group: `supply_chain`
- maps_to_frameworks: [`NIST-SSDF:PW.4.4`, `EU-CRA:Annex-I`]
- maps_to_controls: [`GEN-SC-01`, `GEN-SC-02`, `GEN-SC-03`]

### Field: outsourced_development
- label: `Development or maintenance outsourced to a third party`
- required: `true`
- field_type: `boolean`
- group: `supply_chain`
- maps_to_frameworks: [`ISO27001:A.5.19`, `MAS-TRM:§9`]
- maps_to_controls: [`GEN-TPR-01`]

### Field: build_system
- label: `CI/CD build system`
- required: `false`
- field_type: `select`
- group: `supply_chain`
- ask_when: `third_party_dependencies == true OR uses_open_source == true`
- options:
  - `github_actions`
  - `gitlab_ci`
  - `azure_devops`
  - `jenkins`
  - `circleci`
  - `other`
  - `no_cicd`
- maps_to_frameworks: [`SLSA:L2`, `NIST-SSDF:PW.4`]

### Field: cra_product_category
- label: `EU CRA product category`
- required: `false`
- field_type: `select`
- group: `compliance_scope`
- ask_when: `eu IN geographic_scope`
- options:
  - `default_product_with_digital_elements`
  - `important_class_i`
  - `important_class_ii`
  - `critical_product`
  - `not_a_product_with_digital_elements`
- help_text: `Classifies whether the product is default, important, or critical under the EU Cyber Resilience Act.`
- maps_to_frameworks: [`EU-CRA:Art.6`, `EU-CRA:Annex-III`, `EU-CRA:Annex-IV`]
- maps_to_controls: [`CRA-VUL-01`, `CRA-SBOM-01`, `CRA-DISC-01`, `CRA-REPORT-01`]

### Field: cra_intended_purpose
- label: `EU CRA intended purpose`
- required: `false`
- field_type: `textarea`
- group: `compliance_scope`
- ask_when: `eu IN geographic_scope`
- help_text: `Describe the product's intended purpose, operating environment, and security assumptions for CRA documentation.`
- maps_to_frameworks: [`EU-CRA:Art.13`]
- maps_to_controls: [`GEN-TPR-01`, `CRA-SBOM-01`]

### Field: mlps_protection_class
- label: `MLPS 2.0 protection class`
- required: `false`
- field_type: `select`
- group: `compliance_scope`
- ask_when: `cn IN geographic_scope`
- options:
  - `level_1`
  - `level_2`
  - `level_3`
  - `level_4`
  - `level_5`
  - `to_be_determined`
- help_text: `China MLPS 2.0 protection class for systems operated in mainland China.`
- maps_to_frameworks: [`MLPS2:§4.1`, `GB/T22239:2019`]
- maps_to_controls: [`MLPS2-IAM-01`, `MLPS2-LOG-01`, `GEN-BCP-01`]

### Field: regulatory_obligations
- label: `Known regulatory obligations (select all that apply)`
- required: `false`
- field_type: `multiselect`
- group: `compliance_scope`
- options:
  - `gdpr`
  - `pipl`
  - `hipaa`
  - `pci_dss`
  - `sox`
  - `fisma`
  - `mas_notice`
  - `dpdpa`
  - `lgpd`
  - `other`
- help_text: `Select any known obligations. The agent will also infer likely obligations from geographic_scope and data_classification.`
- maps_to_controls: [`GEN-PRV-01`, `GEN-PRV-02`, `GEN-ENC-02`, `GEN-VUL-02`]
