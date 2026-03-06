"""Tests for assessment API (LLM mocked)."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.assessment import AssessmentReport, ReportMetadata


def _make_report(task_id):
    return AssessmentReport(
        task_id=str(task_id),
        status="completed",
        summary="Test summary",
        risk_items=[],
        compliance_gaps=[],
        remediations=[],
        metadata=ReportMetadata(
            scenario_id=None,
            project_id=None,
            model_used="ollama",
            completed_at=datetime.now(timezone.utc),
        ),
    )


def test_submit_assessment_no_files_422(client):
    """POST /api/v1/assessments without files returns 422 (validation error)."""
    r = client.post("/api/v1/assessments")
    assert r.status_code == 422


def test_submit_assessment_with_txt_file(client):
    """POST /api/v1/assessments with a text file returns 200 and task_id (LLM mocked)."""
    async def mock_run_assessment(task_id, parsed_documents, scenario_id=None, project_id=None):
        return _make_report(task_id)

    with patch("app.api.assessments.run_assessment", new_callable=AsyncMock, side_effect=mock_run_assessment):
        files = [("files", ("sample.txt", b"Security questionnaire answer: Yes.", "text/plain"))]
        r = client.post("/api/v1/assessments", data={"scenario_id": "default"}, files=files)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "accepted"
    assert "task_id" in data
    task_id = data["task_id"]
    r2 = client.get(f"/api/v1/assessments/{task_id}")
    assert r2.status_code == 200
    r2_data = r2.json()
    assert r2_data.get("status") == "completed"
    assert r2_data.get("report") is not None


def test_get_assessment_not_found_404(client):
    """GET /api/v1/assessments/{id} for unknown id returns 404."""
    r = client.get("/api/v1/assessments/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
