# Phase 5: Security Control Verification — AI & ML Specific Controls

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase5_control_verify_ai`
- phase: `5`
- phase_name: `Security Control Verification — AI/ML`
- parent_agent: `control_verification_agent`
- schema_type: `controls`
- purpose: `AI and machine learning–specific security and governance controls. Loaded in addition to phase5_control_verify when involves_ai_ml is true.`
- load_condition: `phase1_intake.involves_ai_ml == true`

## Framework Mappings

- OWASP LLM Top 10 2025
- NIST AI RMF 1.0 (GOVERN, MAP, MEASURE, MANAGE)
- EU AI Act Art. 9–17 (high-risk AI obligations)
- ISO/IEC 42001:2023 (AI Management System)
- ISO/IEC 5338:2023 (AI lifecycle processes)

---

## Controls

### Control: AI-SEC-01
- control_id: `AI-SEC-01`
- family: `AI Security`
- title: `Prompt injection prevention`
- normalized_requirement: `LLM-based applications must implement controls to detect and mitigate prompt injection attacks, including indirect prompt injection through external data sources. System prompts must be treated as security boundaries.`
- frameworks:
  - `OWASP-LLM:LLM01`
  - `NIST-AIRMF:MEASURE.2.5`
- ai_only: `true`
- expected_evidence:
  - `Prompt injection test cases and results`
  - `Input sanitization or instruction hierarchy implementation evidence`
  - `System prompt separation from user input evidence`
- review_focus:
  - `Is user input processed separately from system instructions?`
  - `Are external data sources (RAG, tools, APIs) treated as untrusted?`
  - `Is there monitoring for prompt injection attempts in production?`

### Control: AI-SEC-02
- control_id: `AI-SEC-02`
- family: `AI Security`
- title: `Model integrity and provenance`
- normalized_requirement: `AI models in production must have verifiable provenance: source, version, license, and integrity hash documented. Model artifacts must be stored with access controls and change management.`
- frameworks:
  - `NIST-AIRMF:MAP.2.2`
  - `ISO-42001:§8.4`
  - `EU-AIAct:Art.11`
- ai_only: `true`
- expected_evidence:
  - `Model registry entry with version, hash, and source`
  - `Model access control configuration`
  - `Change management record for model updates`
- review_focus:
  - `Is model provenance documented and verifiable?`
  - `Are model updates subject to the same review process as code changes?`

### Control: AI-SEC-03
- control_id: `AI-SEC-03`
- family: `AI Security`
- title: `Training data validation and poisoning prevention`
- normalized_requirement: `Training and fine-tuning datasets must be validated for quality, integrity, and absence of malicious content. Data collection processes must prevent adversarial data poisoning.`
- frameworks:
  - `EU-AIAct:Art.10`
  - `NIST-AIRMF:MAP.1.5`
  - `ISO-42001:§8.4`
- ai_only: `true`
- expected_evidence:
  - `Data validation pipeline or data quality report`
  - `Training data source attestation`
  - `Data poisoning detection approach description`
- review_focus:
  - `Is training data sourced from trusted, documented sources?`
  - `Are data validation checks automated and logged?`

### Control: AI-SEC-04
- control_id: `AI-SEC-04`
- family: `AI Security`
- title: `Adversarial robustness testing`
- normalized_requirement: `AI models used in high-stakes decisions must be tested for adversarial robustness: resistance to adversarial examples, model inversion, and membership inference attacks appropriate to the deployment context.`
- frameworks:
  - `NIST-AIRMF:MEASURE.2.6`
  - `EU-AIAct:Art.9`
  - `ISO-42001:§9.1`
- ai_only: `true`
- load_condition: `phase1_intake.ai_eu_risk_class IN [high, unacceptable]`
- expected_evidence:
  - `Adversarial robustness test report`
  - `Red-team or adversarial evaluation methodology`
  - `Robustness metrics and accepted thresholds`
- review_focus:
  - `Has the model been tested against adversarial inputs relevant to its deployment context?`
  - `Are robustness thresholds defined and met?`

### Control: AI-SEC-05
- control_id: `AI-SEC-05`
- family: `AI Security`
- title: `AI model output monitoring`
- normalized_requirement: `AI model outputs in production must be monitored for anomalies, unexpected behavior, model drift, and potential misuse. Monitoring results must be regularly reviewed.`
- frameworks:
  - `EU-AIAct:Art.12`
  - `NIST-AIRMF:MEASURE.2.8`
  - `ISO-42001:§9.1`
- ai_only: `true`
- expected_evidence:
  - `Model output monitoring dashboard or alerting configuration`
  - `Drift detection implementation evidence`
  - `Monitoring review cadence documentation`
- review_focus:
  - `Is model performance (accuracy, fairness, safety) monitored in production?`
  - `Are anomalous outputs flagged and reviewed?`

### Control: AI-SEC-06
- control_id: `AI-SEC-06`
- family: `AI Security`
- title: `LLM rate limiting and abuse prevention`
- normalized_requirement: `LLM-based applications accessible to external users must implement rate limiting, input size limits, and abuse detection to prevent denial-of-wallet attacks, jailbreaking attempts, and misuse.`
- frameworks:
  - `OWASP-LLM:LLM10`
  - `NIST-AIRMF:MANAGE.2`
- ai_only: `true`
- expected_evidence:
  - `Rate limiting configuration`
  - `Input length/token limits`
  - `Abuse detection or content filtering evidence`
- review_focus:
  - `Is there rate limiting per user or API key to prevent abuse?`
  - `Are jailbreak/harmful content attempts detected and blocked?`

### Control: AI-SEC-07
- control_id: `AI-SEC-07`
- family: `AI Security`
- title: `Bias evaluation and fairness testing`
- normalized_requirement: `AI systems making consequential decisions must be evaluated for bias across relevant demographic and protected groups, with results documented and bias mitigation measures applied where necessary.`
- frameworks:
  - `EU-AIAct:Art.10(2)(f)`
  - `NIST-AIRMF:MEASURE.2.2`
  - `ISO-42001:§8.4`
- ai_only: `true`
- load_condition: `phase1_intake.ai_eu_risk_class IN [high, unacceptable]`
- expected_evidence:
  - `Bias evaluation report with metrics across demographic groups`
  - `Dataset representativeness analysis`
  - `Mitigation measures applied and re-evaluation results`
- review_focus:
  - `Has the model been evaluated for bias relevant to its use case?`
  - `Are bias metrics within acceptable thresholds for the deployment context?`

### Control: AI-GOV-01
- control_id: `AI-GOV-01`
- family: `AI Governance`
- title: `Model card and technical documentation`
- normalized_requirement: `Every AI model in production must be documented with a model card or equivalent, covering: intended use, out-of-scope uses, performance metrics, limitations, training data, and known risks.`
- frameworks:
  - `ISO-42001:§7.5`
  - `EU-AIAct:Art.11`
  - `NIST-AIRMF:GOVERN.4.2`
- ai_only: `true`
- expected_evidence:
  - `Model card document (Hugging Face format, Google Model Card, or equivalent)`
  - `Technical documentation file or system card`
  - `Review and approval record for documentation`
- review_focus:
  - `Is the model card publicly available or accessible to stakeholders?`
  - `Does the documentation cover known limitations and failure modes?`

### Control: AI-GOV-02
- control_id: `AI-GOV-02`
- family: `AI Governance`
- title: `Human oversight mechanism`
- normalized_requirement: `High-risk AI systems must have effective human oversight mechanisms that allow operators to understand, intervene, override, or shut down the system. Automated decisions must be subject to meaningful human review where required.`
- frameworks:
  - `EU-AIAct:Art.14`
  - `NIST-AIRMF:MANAGE.3`
  - `ISO-42001:§8.7`
- ai_only: `true`
- load_condition: `phase1_intake.ai_eu_risk_class IN [high, unacceptable]`
- expected_evidence:
  - `Human oversight workflow or override capability evidence`
  - `Operator training documentation`
  - `Kill switch or model shutdown procedure`
- review_focus:
  - `Can operators effectively monitor and override automated AI decisions?`
  - `Is there a documented procedure to shut down or pause the AI system?`

### Control: AI-GOV-03
- control_id: `AI-GOV-03`
- family: `AI Governance`
- title: `EU AI Act conformity documentation`
- normalized_requirement: `High-risk AI systems placed on the EU market must complete a conformity assessment (Art. 43) and maintain a technical file (Art. 11) including risk management, data governance, transparency, human oversight, accuracy, and cybersecurity documentation.`
- frameworks:
  - `EU-AIAct:Art.11`
  - `EU-AIAct:Art.43`
  - `EU-AIAct:Art.17`
- ai_only: `true`
- load_condition: `phase1_intake.ai_eu_risk_class == high AND eu IN phase1_intake.geographic_scope`
- expected_evidence:
  - `EU AI Act technical file or conformity assessment record`
  - `CE marking or notified body involvement record (if applicable)`
  - `Quality management system (Art. 17) documentation`
- review_focus:
  - `Is the technical file complete and aligned to EU AI Act Annex IV?`
  - `Has a conformity assessment been completed per Art. 43?`
