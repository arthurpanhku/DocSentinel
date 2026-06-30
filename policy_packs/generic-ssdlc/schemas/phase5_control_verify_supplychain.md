# Phase 5: Security Control Verification — Supply Chain Controls

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase5_control_verify_supplychain`
- phase: `5`
- phase_name: `Security Control Verification — Supply Chain`
- parent_agent: `control_verification_agent`
- schema_type: `controls`
- purpose: `Supply chain–specific security controls. Loaded in addition to phase5_control_verify when third_party_dependencies or uses_open_source is true.`
- load_condition: `phase1_intake.third_party_dependencies == true OR phase1_intake.uses_open_source == true`

## Framework Mappings

- EU CRA Art. 13(5) — SBOM requirements for products with digital elements
- NIST SSDF PW.4 — reuse existing well-secured software
- EO 14028 §4(e) — software supply chain security (US federal)
- SLSA L1–L4 — supply chain levels for software artifacts
- CIS Controls v8 #2, #16 — software asset inventory and security

---

## Controls

### Control: GEN-SC-01
- control_id: `GEN-SC-01`
- family: `Supply Chain`
- title: `SBOM generation and maintenance`
- normalized_requirement: `A Software Bill of Materials (SBOM) must be generated for each release in a machine-readable format (CycloneDX or SPDX), covering all direct and transitive dependencies, and kept current throughout the product lifecycle.`
- frameworks:
  - `EU-CRA:Art.13(5)`
  - `NIST-SSDF:PW.4`
  - `EO-14028:§4(e)`
  - `NTIA:SBOM-minimum-elements`
- expected_evidence:
  - `CycloneDX JSON/XML or SPDX SBOM file`
  - `SBOM generation pipeline step in CI/CD`
  - `SBOM update cadence policy`
- review_focus:
  - `Does the SBOM cover all direct and transitive dependencies?`
  - `Is SBOM generation automated as part of every build?`
  - `Does the SBOM meet NTIA minimum element requirements (supplier, component, version, unique ID, dependency relationship, author, timestamp)?`

### Control: GEN-SC-02
- control_id: `GEN-SC-02`
- family: `Supply Chain`
- title: `Build pipeline integrity (SLSA)`
- normalized_requirement: `The build pipeline must achieve at minimum SLSA Level 1 (build scripted and logged) for all projects, and SLSA Level 2 (hosted, versioned build service with provenance) for internet-facing or regulated systems.`
- frameworks:
  - `SLSA:L1-L4`
  - `NIST-SSDF:PW.4.1`
  - `EU-CRA:Annex-I`
  - `CIS-v8:#2`
- expected_evidence:
  - `SLSA provenance attestation (DSSE/in-toto) or equivalent`
  - `Build configuration stored in version control`
  - `Access controls on CI/CD pipeline and build environment`
- review_focus:
  - `Is the build defined in version-controlled scripts, not manual steps?`
  - `Is the build service isolated from developer workstations?`
  - `Are build provenance attestations generated and verifiable?`

### Control: GEN-SC-03
- control_id: `GEN-SC-03`
- family: `Supply Chain`
- title: `Dependency vulnerability management`
- normalized_requirement: `All software dependencies must be inventoried and continuously monitored for newly disclosed vulnerabilities. Critical CVEs must be remediated within 30 days; high CVEs within 90 days, or formally risk-accepted.`
- frameworks:
  - `NIST-SSDF:PW.4.4`
  - `OWASP-Top10:A06`
  - `EU-CRA:Annex-I:§1(e)`
  - `CIS-v8:#16.13`
- expected_evidence:
  - `SCA or dependency scan report`
  - `Automated update tooling (Dependabot, Renovate, or equivalent) evidence`
  - `Open finding count with age and SLA compliance`
- review_focus:
  - `Is there automated alerting when new CVEs affect in-use dependencies?`
  - `Are all critical CVEs remediated or formally risk-accepted within SLA?`
  - `Is the dependency inventory complete and regularly updated?`
