from scripts.validate_pr_plan import classify_risk, validate_pr_plan

VALID_BODY = """
Fixes #31

## Plan
Implement the contract, tests, and migration in independently reviewable commits.

## Security impact
Authentication and authorization boundaries are covered by denied-path tests.

## Risk and rollback
The migration has a downgrade and the feature can be disabled with configuration.

## How to Verify
Run backend tests, contract checks, and the frontend build before merge.
"""


def test_valid_high_risk_plan_passes():
    assert validate_pr_plan(VALID_BODY, ["app/core/deps.py"]) == []


def test_high_risk_plan_requires_security_and_rollback():
    body = """
Relates to #31
## Plan
Implement and test the requested documentation-only behavior carefully.
## How to Verify
Run the documented verification command and inspect its generated output.
"""
    errors = validate_pr_plan(body, ["app/api/assessments.py"])
    assert any("Security impact" in error for error in errors)
    assert any("Risk and rollback" in error for error in errors)


def test_issue_link_is_required():
    errors = validate_pr_plan(VALID_BODY.replace("Fixes #31", "No issue"), [])
    assert errors == ["Link an issue with 'Fixes #N' or 'Relates to #N'."]


def test_untouched_template_placeholders_fail():
    body = """
Fixes #31
## Plan | 实施计划
- [ ] Describe the bounded implementation steps and affected contracts.
## Security impact | 安全影响
Describe changes to trust boundaries, authentication, authorization, data.
## Risk and rollback | 风险与回滚
State failure modes, migration compatibility, and the concrete rollback path.
## How to Verify | 如何验证
**Steps to test the change** and inspect it.
"""
    assert len(validate_pr_plan(body, ["app/core/security.py"])) == 4


def test_each_risk_tier_is_deterministic():
    assert classify_risk(["docs/README.md"]) == "low"
    assert classify_risk(["frontend/src/App.tsx"]) == "medium"
    assert classify_risk(["app/services/evidence_gate.py"]) == "high"
    assert classify_risk(["alembic/versions/new.py"]) == "critical"
    assert classify_risk(["docs/README.md", "app/core/security.py"]) == "critical"
