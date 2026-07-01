# Phase 3: Secure Design Review

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase3_design_review`
- phase: `3`
- phase_name: `Secure Design Review`
- parent_agent: `design_review_agent`
- schema_type: `fields`
- purpose: `Review design artifacts — API contracts, cryptographic choices, authentication design, data handling — before implementation begins to catch security flaws at the lowest cost point.`

## Agent Guidance

- Review OpenAPI/Swagger specs for insecure endpoint patterns (missing auth, over-privileged scopes, lack of rate limiting).
- Validate cryptographic algorithm choices against NIST-approved algorithms (SP 800-131A Rev 2).
- Check authentication design against NIST 800-63B AAL requirements.
- For CN-scoped systems, check data residency and PIPL Art. 51 privacy-by-design.
- For SG financial systems, apply MAS TRM §4.2 design controls.
- For EU AI high-risk systems, apply EU AI Act Art. 10 data governance requirements.

## Framework Mappings

- NIST SSDF PW.2.2 — review software design
- NIST SP 800-63B — digital identity guidelines for authentication design
- NIST SP 800-131A Rev 2 — cryptographic algorithm transitions
- EU AI Act Art. 10 — data governance and data quality for training datasets
- China PIPL Art. 51 — privacy by design
- ISO/IEC 27001:2022 A.8.25 — secure development lifecycle
- Singapore MAS TRM §4.2 — system design and architecture controls

## Fields

### Field: api_spec_file
- label: `API specification (OpenAPI / Swagger)`
- required: `false`
- field_type: `file_upload`
- group: `api_design`
- help_text: `Upload an OpenAPI 3.x or Swagger 2.x YAML/JSON file. The agent will check for missing authentication, insecure transport, over-exposed endpoints, and lack of rate limiting.`
- maps_to_frameworks: [`OWASP-API:API1`, `OWASP-API:API3`, `NIST-SSDF:PW.2`]

### Field: authentication_design
- label: `Authentication design description`
- required: `true`
- field_type: `textarea`
- group: `identity_design`
- help_text: `Describe the authentication mechanism: IdP used, SSO protocol (SAML/OIDC), MFA requirements, session management approach, and any machine-to-machine auth.`
- maps_to_frameworks: [`NIST-800-63B:AAL`, `ISO27001:A.9.4`, `OWASP-ASVS:V2`]

### Field: authorization_design
- label: `Authorization design description`
- required: `true`
- field_type: `textarea`
- group: `identity_design`
- help_text: `Describe role/permission model, access control enforcement points, and any attribute-based or policy-based access control.`
- maps_to_frameworks: [`NIST-800-53:AC`, `OWASP-ASVS:V4`]

### Field: cryptography_design
- label: `Cryptographic design choices`
- required: `true`
- field_type: `textarea`
- group: `cryptography`
- help_text: `List algorithms used: TLS version, cipher suites, hashing algorithms, symmetric/asymmetric encryption, key lengths, and key management approach.`
- maps_to_frameworks: [`NIST-800-131A`, `ISO27001:A.8.24`, `FIPS-140-2`]

### Field: data_flow_privacy
- label: `Data handling and privacy design`
- required: `true`
- field_type: `textarea`
- group: `data_privacy`
- help_text: `Describe where PII is collected, processed, stored, and deleted. Include consent mechanisms, data minimization strategy, and retention periods.`
- maps_to_frameworks: [`GDPR:Art.25`, `PIPL:Art.51`, `ISO27001:A.5.34`]

### Field: secure_defaults
- label: `Security defaults and fail-secure design`
- required: `false`
- field_type: `textarea`
- group: `resilience`
- help_text: `Describe how the system fails safely: error handling, fallback behavior, default-deny configurations.`
- maps_to_frameworks: [`NIST-SSDF:PW.5`, `OWASP-ASVS:V1.7`]

### Field: ai_data_governance
- label: `AI training data governance and quality controls`
- required: `false`
- field_type: `textarea`
- group: `ai_design`
- ask_when: `phase1_intake.involves_ai_ml == true`
- help_text: `Describe data quality checks, bias mitigation, labeling processes, and documentation for training/validation datasets.`
- maps_to_frameworks: [`EU-AIAct:Art.10`, `ISO-42001:§8.4`, `NIST-AIRMF:MAP.1`]
