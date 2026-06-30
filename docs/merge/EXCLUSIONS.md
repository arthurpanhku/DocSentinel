# PallasGuard Merge Exclusions

This file records the Phase 0 exclusion policy for merging PallasGuard
governance capabilities into DocSentinel.

## Reference Source

- PallasGuard is used only as a local reference under `_pallasguard_src/`.
- `_pallasguard_src/` is ignored by git and must not be committed.
- The cloned public PallasGuard repository did not contain the merge plan file
  named in the work order. The attached merge plan text was read in full before
  Phase 0 work began, and this local reference tree is used only for source
  inspection.

## Excluded Source Material

Do not copy, paraphrase, or migrate content from these PallasGuard areas:

- The proprietary platform integration package under
  `_pallasguard_src/backend/app/integrations/`.
- The root field-reference document in `_pallasguard_src/`.
- The export catalog helper script in `_pallasguard_src/scripts/`.
- Proprietary integration specifications under
  `_pallasguard_src/docs/40_integrations/`.
- Any policy pack directories that are private, local-only, internal, or marked
  private by name.

## Allowed Policy Pack Scope

Only the public policy pack content may be considered for later phases:

- `_pallasguard_src/policy_packs/generic-ssdlc/`
- `_pallasguard_src/policy_packs/overlays/nist-ssdf/`
- `_pallasguard_src/policy_packs/overlays/singapore-mas-trm/`
- `_pallasguard_src/policy_packs/overlays/iso-27001-2022/`
- `_pallasguard_src/policy_packs/overlays/eu-ai-act/`
- `_pallasguard_src/policy_packs/overlays/iso-42001/`
- `_pallasguard_src/policy_packs/overlays/china-mlps2/`
- `_pallasguard_src/policy_packs/overlays/owasp-samm/`
- `_pallasguard_src/policy_packs/overlays/eu-cra/`
- `_pallasguard_src/policy_packs/framework-template/`
- `_pallasguard_src/policy_packs/tools/`

## Review Rule

Every phase must run the required sensitive-content grep against `app/`,
`docs/`, `policy_packs/`, and `frontend/`. Any match blocks progress and must be
removed before committing.
