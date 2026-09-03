from datetime import UTC, datetime

import pytest
from sqlmodel import create_engine

import app.models  # noqa: F401
from app.models.assessment import AssessmentReport, ReportMetadata
from app.models.parser import ParsedDocument, ParsedDocumentMetadata
from app.services.assessment_service import AssessmentService, TaskNotFoundError
from app.services.assessment_store import SqlAssessmentTaskStore


def _document() -> ParsedDocument:
    return ParsedDocument(
        content="MFA is required for administrative access.",
        metadata=ParsedDocumentMetadata(filename="policy.md", type="md"),
    )


async def _runner(task_id, parsed_documents, **kwargs) -> AssessmentReport:
    return AssessmentReport(
        version="2.0",
        task_id=str(task_id),
        status="completed",
        summary="Persistent assessment",
        risk_items=[],
        compliance_gaps=[],
        remediations=[],
        confidence=0.9,
        sources=[],
        metadata=ReportMetadata(
            model_used="test",
            completed_at=datetime.now(UTC),
        ),
    )


@pytest.mark.asyncio
async def test_tasks_survive_service_restart_and_are_tenant_scoped(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'tasks.db'}")
    store = SqlAssessmentTaskStore(engine, create_tables=True)
    service = AssessmentService(store=store)

    created = await service.submit(
        [_document()],
        runner=_runner,
        tenant_id="tenant-a",
        submitted_by_id=7,
        idempotency_key="request-1",
    )
    result = await service.wait_for_terminal(str(created.task_id), 2)
    assert result.status == "review_pending"

    restarted = AssessmentService(store=SqlAssessmentTaskStore(engine))
    restored = restarted.get(str(created.task_id), tenant_id="tenant-a")
    assert restored.report is not None
    assert restored.report.summary == "Persistent assessment"
    with pytest.raises(TaskNotFoundError):
        restarted.get(str(created.task_id), tenant_id="tenant-b")

    duplicate = await restarted.submit(
        [_document()],
        runner=_runner,
        tenant_id="tenant-a",
        idempotency_key="request-1",
    )
    assert duplicate.task_id == created.task_id
    assert len(store.list(tenant_id="tenant-a")) == 1
