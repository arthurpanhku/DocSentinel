"""Compatibility spreadsheet contracts for security intake and control review."""

# Phase 1 compatibility sheet "Intake" (two columns: field_key, value)
GATE1_ISAF_FIELD_KEYS: list[str] = [
    "project_name",
    "project_owner",
    "business_unit",
    "go_live_date",
    "system_description",
    "data_classification",
    "user_base",
    "deployment_environment",
    "hosting_model",
    "third_party_integrations",
    "authentication_method",
    "authorization_model",
    "encryption_in_transit",
    "encryption_at_rest",
    "pii_data_present",
    "regulatory_scope",
    "change_type",
    "risk_owner",
]

# Phase 1 compatibility sheet "SecurityQuestionnaire" (question_key, answer)
GATE1_QUESTION_KEYS: list[str] = [f"q{i}" for i in range(1, 23)]

GATE1_SHEET_ISAF = "Intake"
GATE1_SHEET_QUESTIONNAIRE = "SecurityQuestionnaire"

# Control review sheet, header row must match (order matters)
SCD_SHEET_NAME = "Security Control Document"
SCD_COLUMN_HEADERS: list[str] = [
    "Requirement ID",
    "Domain",
    "Requirement Text",
    "Implementation Guidance",
    "Applicability",
    "Risk Level",
    "Evidence Description",
    "Evidence Reference",
    "Implementation Status",
    "Reviewer Notes",
    "Review Status",
    "Review Date",
    "Reviewer Name",
]

# Keys used inside RequirementRow.scd_extras JSON
SCD_EXTRAS_IMPLEMENTATION = "implementation_status"
SCD_EXTRAS_REVIEW_DATE = "review_date"
SCD_EXTRAS_REVIEWER_NAME = "reviewer_name"
