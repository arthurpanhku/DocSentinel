from pathlib import Path
from uuid import UUID

import pytest

from app.models.assessment import AssessmentReport, Vulnerability
from app.models.parser import ParsedDocument
from evals.adapters.owasp_benchmark import to_cases
from evals.models import RunConfig
from evals.runner.run_eval import run_cases

FIXTURE = Path(__file__).parent / "fixtures" / "owasp_benchmark"


async def _deterministic_runner(
    task_id: UUID,
    parsed_documents: list[ParsedDocument],
    **_: object,
) -> AssessmentReport:
    filename = parsed_documents[0].metadata.filename
    vulnerabilities = []
    if filename == "BenchmarkTest00001.java":
        vulnerabilities.append(
            Vulnerability(
                id="v1",
                title="Path traversal",
                severity="high",
                cwe_id="CWE-22",
            )
        )
    return AssessmentReport(
        task_id=str(task_id),
        phase="testing",
        status="completed",
        summary="deterministic eval report",
        vulnerabilities=vulnerabilities,
    )


@pytest.mark.asyncio
async def test_runner_writes_stable_scorecards_with_assessment_service(tmp_path):
    cases = list(to_cases(FIXTURE))
    cfg = RunConfig(
        run_id="fixture-run",
        dataset_id="owasp_benchmark",
        repeats=1,
        provider="fixture",
        model_id="deterministic",
    )

    first = await run_cases(
        cases,
        cfg,
        input_root=FIXTURE,
        report_root=tmp_path,
        assessment_runner=_deterministic_runner,
    )
    second = await run_cases(
        cases,
        cfg.model_copy(update={"run_id": "fixture-run-2"}),
        input_root=FIXTURE,
        report_root=tmp_path,
        assessment_runner=_deterministic_runner,
    )

    assert first["metrics"] == second["metrics"]
    assert first["metrics"]["accuracy"] == 1.0
    assert first["metrics"]["false_positive_rate"] == 0.0
    assert (tmp_path / "fixture-run" / "scorecard.json").exists()
    assert (tmp_path / "fixture-run" / "scorecard.md").exists()

