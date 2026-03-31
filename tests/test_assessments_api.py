"""Tests for assessment API (LLM mocked)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.models.assessment import AssessmentReport, Remediation, ReportMetadata, SourceCitation


def _make_report(task_id):
    return AssessmentReport(
        version="2.0",
        task_id=str(task_id),
        status="completed",
        summary="Test summary",
        risk_items=[],
        compliance_gaps=[],
        remediations=[],
        confidence=0.93,
        sources=[
            SourceCitation(
                id="S1",
                file="policy.pdf",
                page=12,
                paragraph_id="p-1",
                excerpt="MFA is required for privileged access.",
                evidence_link="policy.pdf#p-1",
                score=0.89,
            )
        ],
        metadata=ReportMetadata(
            scenario_id=None,
            project_id=None,
            model_used="ollama",
            completed_at=datetime.now(timezone.utc),
        ),
    )


def _make_report_with_remediation(task_id):
    r = _make_report(task_id)
    r.remediations = [
        Remediation(
            id="R1",
            action="Create GitHub issue for missing MFA policy",
            priority="high",
            related_risk_ids=["risk-1"],
            related_gap_ids=["gap-1"],
        )
    ]
    return r


def test_submit_assessment_no_files_422(client):
    """POST /api/v1/assessments without files returns 422 (validation error)."""
    r = client.post("/api/v1/assessments")
    assert r.status_code == 422


def test_submit_assessment_with_txt_file(client):
    """
    POST /api/v1/assessments with a text file returns 200 and task_id (LLM mocked).
    """

    async def mock_run_assessment(
        task_id, parsed_documents, scenario_id=None, project_id=None, skill_id=None
    ):
        return _make_report(task_id)

    with patch(
        "app.api.assessments.run_assessment",
        new_callable=AsyncMock,
        side_effect=mock_run_assessment,
    ):
        files = [
            (
                "files",
                ("sample.txt", b"Security questionnaire answer: Yes.", "text/plain"),
            )
        ]
        r = client.post(
            "/api/v1/assessments", data={"scenario_id": "default"}, files=files
        )
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "accepted"
    assert "task_id" in data
    task_id = data["task_id"]
    r2 = client.get(f"/api/v1/assessments/{task_id}")
    assert r2.status_code == 200
    r2_data = r2.json()
    assert r2_data.get("status") in {"review_pending", "completed"}
    assert r2_data.get("report") is not None
    assert "confidence" in r2_data.get("report", {})
    assert "sources" in r2_data.get("report", {})


def test_submit_assessment_with_skill(client):
    """POST /api/v1/assessments with skill_id passes it to orchestrator."""

    # Mock to capture arguments
    captured_args = {}
    async def mock_run_assessment(
        task_id, parsed_documents, scenario_id=None, project_id=None, skill_id=None
    ):
        captured_args["skill_id"] = skill_id
        return _make_report(task_id)

    with patch(
        "app.api.assessments.run_assessment",
        new_callable=AsyncMock,
        side_effect=mock_run_assessment,
    ):
        files = [("files", ("sample.txt", b"Content", "text/plain"))]
        client.post(
            "/api/v1/assessments",
            data={"skill_id": "iso-27001-auditor"},
            files=files
        )

    assert captured_args.get("skill_id") == "iso-27001-auditor"


def test_review_comment_and_activity_flow(client):
    async def mock_run_assessment(
        task_id, parsed_documents, scenario_id=None, project_id=None, skill_id=None
    ):
        return _make_report(task_id)

    with patch(
        "app.api.assessments.run_assessment",
        new_callable=AsyncMock,
        side_effect=mock_run_assessment,
    ):
        files = [("files", ("sample.txt", b"Content", "text/plain"))]
        r = client.post(
            "/api/v1/assessments",
            data={"collaborative_mode": True},
            files=files
        )
        created = r.json()
        task_id = created["task_id"]

    # 1. Check status is review_pending
    r_check = client.get(f"/api/v1/assessments/{task_id}")
    assert r_check.json()["status"] == "review_pending"

    # 2. Add comment
    client.post(
        f"/api/v1/assessments/{task_id}/comments",
        json={"content": "Looks risky", "user_id": "auditor_1"}
    )

    # 3. Approve
    client.post(
        f"/api/v1/assessments/{task_id}/review",
        json={"action": "approve", "comment": "LGTM", "assignee": "manager"}
    )

    # 4. Verify final state
    r_final = client.get(f"/api/v1/assessments/{task_id}")
    data = r_final.json()
    assert data["status"] == "approved"
    assert data["assignee"] == "manager"

    # Check activity log
    r_act = client.get(f"/api/v1/assessments/{task_id}/activity")
    activity = r_act.json()
    assert any(a["type"] == "comment_added" for a in activity)
    assert any(a["type"] == "review_action" and a["action"] == "approve" for a in activity)


def test_get_assessment_not_found_404(client):
    """GET /api/v1/assessments/{id} for unknown id returns 404."""
    r = client.get("/api/v1/assessments/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_review_console_list_and_remediation_tracking(client):
    async def mock_run_assessment(
        task_id, parsed_documents, scenario_id=None, project_id=None, skill_id=None
    ):
        return _make_report_with_remediation(task_id)

    with patch(
        "app.api.assessments.run_assessment",
        new_callable=AsyncMock,
        side_effect=mock_run_assessment,
    ):
        files = [("files", ("sample.txt", b"Content", "text/plain"))]
        r = client.post("/api/v1/assessments", files=files)
        task_id = r.json()["task_id"]

    r_list = client.get("/api/v1/assessments?limit=200")
    assert r_list.status_code == 200
    ids = {x["task_id"] for x in r_list.json()}
    assert task_id in ids

    r_rems = client.get(f"/api/v1/assessments/{task_id}/remediations")
    assert r_rems.status_code == 200
    rems = r_rems.json()
    assert len(rems) == 1
    assert rems[0]["remediation"]["id"] == "R1"
    assert rems[0]["tracking"]["status"] == "open"

    r_upd = client.post(
        f"/api/v1/assessments/{task_id}/remediations/R1",
        json={
            "status": "in_progress",
            "owner": "dev_1",
            "external_ticket": "https://github.com/org/repo/issues/1",
            "notes": "Working on it",
            "evidence_refs": ["pr#123", "policy-link"],
        },
    )
    assert r_upd.status_code == 200
    upd = r_upd.json()
    assert upd["remediation_id"] == "R1"
    assert upd["status"] == "in_progress"
    assert upd["owner"] == "dev_1"

    r_rems2 = client.get(f"/api/v1/assessments/{task_id}/remediations")
    rems2 = r_rems2.json()
    assert rems2[0]["tracking"]["status"] == "in_progress"
    assert rems2[0]["tracking"]["external_ticket"] == "https://github.com/org/repo/issues/1"
