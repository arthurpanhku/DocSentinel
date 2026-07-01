# Phase 5: Security Control Verification

**Schema Version:** 1.0.0
**Last Updated:** 2026-06-04

## Node

- node_key: `phase5_control_verify`
- phase: `5`
- phase_name: `Security Control Verification`
- parent_agent: `control_verification_agent`
- schema_type: `controls`
- purpose: `Verify implemented security controls through evidence review. AI agent scores each control as IMPLEMENTED / PARTIAL / NOT_IMPLEMENTED / NOT_APPLICABLE based on submitted evidence.`

## Control Scoring

- `IMPLEMENTED` — evidence clearly demonstrates the control is in place
- `PARTIAL` — evidence exists but is incomplete or covers only part of the requirement
- `NOT_IMPLEMENTED` — no evidence; control is required but not yet addressed
- `NOT_APPLICABLE` — project context rules out this control (agent provides rationale)

## Framework Mappings

- NIST SSDF RV.1.1 — identify and confirm vulnerabilities
- NIST AI RMF MEASURE 2.5 — measure AI system performance and risk
- EU AI Act Art. 17 — quality management system for high-risk AI
- ISO/IEC 27001:2022 Annex A — applicable controls across all families
- China MLPS 2.0 — second-level and above security controls
- OWASP SAMM Verification Practice 1 — security testing

---

## Controls

### Control: GEN-IAM-01
- control_id: `GEN-IAM-01`
- family: `Identity & Access`
- title: `Centralized identity and strong authentication`
- normalized_requirement: `The system must use a trusted identity provider and require strong authentication for interactive users, with stronger controls (MFA, hardware tokens, or equivalent) for privileged access.`
- frameworks:
  - `NIST-800-53:IA-2`
  - `ISO27001:A.9.4.2`
  - `OWASP-ASVS:V2.1`
  - `CIS-v8:#6`
- expected_evidence:
  - `Identity provider configuration or screenshot`
  - `MFA enforcement policy or conditional access rule`
  - `Authentication flow diagram or test evidence`
- review_focus:
  - `Is authentication centralized rather than using custom/local credential stores?`
  - `Is MFA enforced for all users and especially for privileged/admin paths?`
  - `Are exceptions to MFA explicitly approved and time-bound?`

### Control: GEN-IAM-02
- control_id: `GEN-IAM-02`
- family: `Identity & Access`
- title: `Role-based authorization and least privilege`
- normalized_requirement: `The system must define roles and permissions so users receive only the access required for their responsibilities, with privileged roles explicitly approved and periodically reviewed.`
- frameworks:
  - `NIST-800-53:AC-2`
  - `ISO27001:A.9.2.2`
  - `OWASP-ASVS:V4.1`
  - `CIS-v8:#6`
- expected_evidence:
  - `Role and permission matrix`
  - `Access approval workflow or ticketing evidence`
  - `Periodic entitlement review record`
- review_focus:
  - `Are roles mapped to business responsibilities rather than individual users?`
  - `Is privileged access time-bound or subject to periodic review?`
  - `Are default-deny configurations in place?`

### Control: GEN-IAM-03
- control_id: `GEN-IAM-03`
- family: `Identity & Access`
- title: `Privileged access management`
- normalized_requirement: `Privileged account credentials must be vaulted in an approved Privileged Access Management (PAM) system. All privileged sessions should be recorded or monitored where feasible.`
- frameworks:
  - `CIS-v8:#5`
  - `NIST-800-53:AC-17`
  - `ISO27001:A.9.2.3`
- expected_evidence:
  - `PAM solution configuration or enrollment screenshot`
  - `Privileged account inventory`
  - `Session recording policy or evidence`
- review_focus:
  - `Are all privileged credentials stored in PAM rather than shared spreadsheets or scripts?`
  - `Is privileged access reviewed and revoked promptly when roles change?`

### Control: GEN-LOG-01
- control_id: `GEN-LOG-01`
- family: `Logging & Monitoring`
- title: `Security event logging`
- normalized_requirement: `Systems must log security-relevant events including authentication, authorization decisions, administrative actions, configuration changes, errors, and security alerts, with sufficient context to support investigation.`
- frameworks:
  - `NIST-800-53:AU-2`
  - `ISO27001:A.8.15`
  - `OWASP-ASVS:V7.1`
  - `CIS-v8:#8`
- expected_evidence:
  - `Logging design or event catalog`
  - `Sample security log entries (with sensitive data masked)`
  - `Monitoring dashboard or alert rule evidence`
- review_focus:
  - `Do log entries include actor, timestamp, source IP, action, and outcome?`
  - `Are authentication, authorization, and admin actions all captured?`
  - `Are sensitive values (passwords, PII, tokens) excluded from logs?`

### Control: GEN-LOG-02
- control_id: `GEN-LOG-02`
- family: `Logging & Monitoring`
- title: `Log retention, time synchronization, and tamper resistance`
- normalized_requirement: `Security logs must be retained for the required operational period, use consistent time synchronization, and be protected from unauthorized modification or deletion.`
- frameworks:
  - `NIST-800-53:AU-9`
  - `ISO27001:A.8.15`
  - `GDPR:Art.32`
- expected_evidence:
  - `Log retention configuration (duration and storage tier)`
  - `Time synchronization configuration (NTP or equivalent)`
  - `Log access control settings or immutability configuration`
- review_focus:
  - `Can administrators alter or delete security logs without detection?`
  - `Are timestamps consistent across all components and services?`
  - `Is retention duration compliant with applicable regulatory requirements?`

### Control: GEN-ENC-01
- control_id: `GEN-ENC-01`
- family: `Cryptography`
- title: `Encryption in transit`
- normalized_requirement: `All network communication carrying authenticated, confidential, or session traffic must use current, approved transport encryption (TLS 1.2 minimum, TLS 1.3 preferred) with valid certificates and secure configuration.`
- frameworks:
  - `NIST-800-52r2`
  - `ISO27001:A.8.24`
  - `OWASP-ASVS:V9.1`
  - `PCI-DSS:6.4.3`
- expected_evidence:
  - `TLS configuration or SSL Labs scan result`
  - `Certificate inventory and renewal process`
  - `Internal API mTLS or service mesh configuration`
- review_focus:
  - `Are weak TLS versions (1.0, 1.1) and cipher suites disabled?`
  - `Are certificates from a trusted CA with appropriate validity periods?`
  - `Is internal service-to-service traffic also encrypted?`

### Control: GEN-ENC-02
- control_id: `GEN-ENC-02`
- family: `Cryptography`
- title: `Encryption at rest and key management`
- normalized_requirement: `Sensitive data must be encrypted at rest using approved algorithms. Encryption keys must be managed using an approved Key Management System (KMS) with defined rotation policies and access controls.`
- frameworks:
  - `NIST-800-53:SC-28`
  - `ISO27001:A.8.24`
  - `OWASP-ASVS:V6.2`
  - `PCI-DSS:3.5`
- expected_evidence:
  - `Storage/database encryption configuration`
  - `KMS or key vault configuration and access policy`
  - `Key rotation schedule or automation evidence`
- review_focus:
  - `Is encryption enabled for databases, blob storage, and backups?`
  - `Are keys stored separately from the data they protect?`
  - `Are key rotation schedules defined and tested?`

### Control: GEN-VUL-01
- control_id: `GEN-VUL-01`
- family: `Vulnerability Management`
- title: `Static application security testing (SAST) and code review`
- normalized_requirement: `Application code must be analyzed using SAST tools as part of the CI/CD pipeline. Critical and high findings must be triaged and remediated or risk-accepted before production deployment.`
- frameworks:
  - `NIST-SSDF:PW.7.2`
  - `OWASP-SAMM:I-SR-1`
  - `CIS-v8:#16.12`
  - `EU-CRA:Annex-I`
- expected_evidence:
  - `SAST scan report or SARIF output`
  - `CI pipeline configuration showing SAST integration`
  - `Finding triage and remediation tracker`
- review_focus:
  - `Is SAST running automatically on every commit or pull request?`
  - `Are all critical/high findings resolved or formally risk-accepted?`

### Control: GEN-VUL-02
- control_id: `GEN-VUL-02`
- family: `Vulnerability Management`
- title: `Dynamic testing and penetration testing`
- normalized_requirement: `Internet-facing and high-risk applications must undergo DAST or penetration testing before major releases, with findings tracked through remediation.`
- frameworks:
  - `NIST-SSDF:RV.1.1`
  - `OWASP-SAMM:V-PT-2`
  - `PCI-DSS:11.3`
- expected_evidence:
  - `DAST scan report or penetration test report`
  - `Finding remediation record with dates and owners`
  - `Retest evidence for critical/high findings`
- review_focus:
  - `Was testing performed by qualified personnel (internal security or accredited firm)?`
  - `Were all in-scope endpoints and authentication paths tested?`
  - `Are open critical/high findings risk-accepted with documented rationale?`

### Control: GEN-VUL-03
- control_id: `GEN-VUL-03`
- family: `Vulnerability Management`
- title: `Container and infrastructure image scanning`
- normalized_requirement: `Container images and infrastructure-as-code must be scanned for known vulnerabilities before deployment. Base images must be kept current with security patches.`
- frameworks:
  - `CIS-Docker:4.1`
  - `NIST-SSDF:PW.4`
  - `OWASP-SAMM:I-SB-2`
- expected_evidence:
  - `Container image scan report (Trivy, Grype, or equivalent)`
  - `Base image update policy or automation evidence`
  - `IaC scanning configuration (Checkov, tfsec, etc.)`
- review_focus:
  - `Are container images scanned before each deployment?`
  - `Is the base image update process automated or tracked?`

### Control: GEN-SEC-01
- control_id: `GEN-SEC-01`
- family: `Application Security`
- title: `Input validation and output encoding`
- normalized_requirement: `All user-supplied input must be validated against allowlists. Output must be encoded for the context in which it is rendered to prevent injection attacks (SQLi, XSS, command injection).`
- frameworks:
  - `OWASP-Top10:A03`
  - `OWASP-ASVS:V5.1`
  - `NIST-800-53:SI-10`
- expected_evidence:
  - `Input validation implementation evidence (code review finding or test result)`
  - `Output encoding library or framework usage`
  - `Security testing result covering injection attack scenarios`
- review_focus:
  - `Is input validated at every entry point, including internal APIs?`
  - `Is output encoded per rendering context (HTML, JSON, SQL, shell)?`

### Control: GEN-SEC-02
- control_id: `GEN-SEC-02`
- family: `Application Security`
- title: `SSRF and injection prevention`
- normalized_requirement: `Systems must prevent Server-Side Request Forgery (SSRF) by validating and allowlisting outbound requests. All external calls must be validated, authenticated, and limited to approved destinations.`
- frameworks:
  - `OWASP-Top10:A10`
  - `OWASP-ASVS:V12.6`
  - `NIST-800-53:SI-10`
- expected_evidence:
  - `Outbound request allowlist or firewall rule evidence`
  - `Code review or SAST finding showing SSRF mitigations`
- review_focus:
  - `Are outbound HTTP calls restricted to known, approved destinations?`
  - `Are cloud metadata endpoints (169.254.169.254) blocked from user-controlled paths?`

### Control: GEN-BCP-01
- control_id: `GEN-BCP-01`
- family: `Resilience`
- title: `Backup, recovery, and business continuity`
- normalized_requirement: `Systems must have documented and tested backup and recovery procedures with defined RTO and RPO targets aligned to the application's criticality.`
- frameworks:
  - `ISO27001:A.8.13`
  - `NIST-800-53:CP-9`
  - `CIS-v8:#11`
- expected_evidence:
  - `Backup configuration and schedule`
  - `Recovery test result with RTO/RPO evidence`
  - `Business continuity or disaster recovery plan reference`
- review_focus:
  - `Are backups tested by actually restoring them?`
  - `Do RTO/RPO targets meet business and contractual requirements?`

### Control: GEN-PRV-01
- control_id: `GEN-PRV-01`
- family: `Privacy`
- title: `PII handling, consent, and data minimization`
- normalized_requirement: `Personal data must be collected only for specified purposes (data minimization), with appropriate consent mechanisms, and must not be processed beyond the original purpose without additional consent.`
- frameworks:
  - `GDPR:Art.5`
  - `GDPR:Art.7`
  - `PIPL:Art.6`
  - `ISO27001:A.5.34`
- expected_evidence:
  - `Privacy notice / consent mechanism screenshot`
  - `Data mapping showing PII fields and their purpose`
  - `Data minimization evidence (fields collected vs. fields needed)`
- review_focus:
  - `Is a lawful basis documented for every category of personal data processed?`
  - `Are consent mechanisms freely given, specific, and revocable?`

### Control: GEN-PRV-02
- control_id: `GEN-PRV-02`
- family: `Privacy`
- title: `Data retention and deletion`
- normalized_requirement: `Personal and sensitive data must be retained only as long as necessary for its purpose and securely deleted when no longer needed, in accordance with documented retention schedules.`
- frameworks:
  - `GDPR:Art.5(1)(e)`
  - `PIPL:Art.19`
  - `ISO27001:A.8.10`
- expected_evidence:
  - `Data retention schedule or policy`
  - `Automated deletion process or scheduled job evidence`
  - `User-requested deletion workflow (GDPR Art. 17 right to erasure)`
- review_focus:
  - `Is there an automated mechanism to enforce retention limits?`
  - `Can data be deleted on user request within regulatory deadlines?`

### Control: GEN-TPR-01
- control_id: `GEN-TPR-01`
- family: `Third-Party Risk`
- title: `Vendor and third-party security assessment`
- normalized_requirement: `Third-party software, SaaS dependencies, and vendors with access to system data or infrastructure must be covered by a vendor security assessment, with risk documented and accepted before go-live.`
- frameworks:
  - `ISO27001:A.5.19`
  - `EU-CRA:Art.13`
  - `NIST-SSDF:PW.4.4`
  - `CIS-v8:#15`
- expected_evidence:
  - `Vendor cyber risk assessment record or SOC 2 / ISO 27001 certificate`
  - `Third-party component inventory`
  - `Contractual security obligations (DPA, security addendum)`
- review_focus:
  - `Are all in-scope vendors and SaaS providers assessed?`
  - `Is vendor risk status acceptable for go-live, or is residual risk formally accepted?`

### Control: GEN-SC-01
- control_id: `GEN-SC-01`
- family: `Supply Chain`
- title: `SBOM generation and maintenance`
- normalized_requirement: `A Software Bill of Materials (SBOM) must be generated for each release, covering all direct and transitive dependencies, and must be kept current throughout the product lifecycle.`
- frameworks:
  - `EU-CRA:Art.13(5)`
  - `NIST-SSDF:PW.4`
  - `EO-14028:§4(e)`
- expected_evidence:
  - `CycloneDX or SPDX SBOM file`
  - `SBOM generation pipeline configuration`
  - `SBOM update cadence evidence`
- review_focus:
  - `Does the SBOM cover all direct and transitive dependencies?`
  - `Is SBOM generation automated in the CI/CD pipeline?`

### Control: GEN-SC-02
- control_id: `GEN-SC-02`
- family: `Supply Chain`
- title: `Build pipeline integrity (SLSA)`
- normalized_requirement: `The build pipeline must meet a defined SLSA (Supply-chain Levels for Software Artifacts) level, with build provenance attestations generated and verifiable. Minimum SLSA L1 for all projects; L2 for internet-facing or regulated systems.`
- frameworks:
  - `SLSA:L1-L4`
  - `NIST-SSDF:PW.4.1`
  - `EU-CRA:Annex-I`
- expected_evidence:
  - `SLSA provenance attestation or build configuration evidence`
  - `Access controls on build configuration and pipeline`
  - `Artifact signing or checksum verification evidence`
- review_focus:
  - `Is the build process scripted and reproducible (not manual)?`
  - `Is the build service isolated from developer workstations?`

### Control: GEN-SC-03
- control_id: `GEN-SC-03`
- family: `Supply Chain`
- title: `Dependency vulnerability management`
- normalized_requirement: `All software dependencies must be inventoried and continuously monitored for known vulnerabilities. Critical and high CVEs must be tracked and remediated within defined SLAs.`
- frameworks:
  - `NIST-SSDF:PW.4.4`
  - `OWASP-Top10:A06`
  - `EU-CRA:Annex-I:§1(e)`
  - `CIS-v8:#16.13`
- expected_evidence:
  - `SCA/dependency scan report with CVE findings`
  - `Dependency update automation evidence (Dependabot, Renovate, etc.)`
  - `Remediation SLA policy and current open finding count`
- review_focus:
  - `Is there automated alerting for new CVEs affecting in-use dependencies?`
  - `Are critical CVEs remediated within the defined SLA (typically 30 days)?`
