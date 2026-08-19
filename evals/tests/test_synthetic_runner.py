import json
from pathlib import Path
from uuid import UUID

import pytest

from app.models.assessment import (
    AssessmentReport,
    ComplianceGap,
    RiskItem,
    SourceCitation,
)
from app.models.parser import ParsedDocument
from evals.adapters.ssdlc_synthetic import to_cases
from evals.models import RunConfig
from evals.runner.run_eval import run_cases

DATASET = Path(__file__).parents[1] / "datasets" / "ssdlc_synthetic_v1"
BASELINE = (
    Path(__file__).parents[1]
    / "reports"
    / "baselines"
    / "ssdlc-synthetic-oracle-v1.json"
)
CASES = list(to_cases(DATASET))
CASES_BY_FILENAME = {Path(case.inputs[0].path).name: case for case in CASES}


async def _oracle_runner(
    task_id: UUID,
    parsed_documents: list[ParsedDocument],
    **_: object,
) -> AssessmentReport:
    filename = parsed_documents[0].metadata.filename
    case = CASES_BY_FILENAME[filename]
    sources: list[SourceCitation] = []
    risks: list[RiskItem] = []
    gaps: list[ComplianceGap] = []
    for truth in case.ground_truth.risk_items:
        citation_id = f"source-{truth.id}"
        sources.append(
            SourceCitation(
                id=citation_id,
                file=filename,
                excerpt=f"Synthetic evidence for {truth.id}",
                locator=truth.evidence_locators[0],
                source_kind="current_document",
            )
        )
        risks.append(
            RiskItem(
                id=str(truth.id),
                title=str(truth.title),
                severity=truth.severity,
                description=truth.description,
                citation_ids=[citation_id],
            )
        )
    for truth in case.ground_truth.compliance_gaps:
        citation_id = f"source-{truth.id}"
        sources.append(
            SourceCitation(
                id=citation_id,
                file=filename,
                excerpt=f"Synthetic evidence for {truth.id}",
                locator=truth.evidence_locators[0],
                source_kind="current_document",
            )
        )
        gaps.append(
            ComplianceGap(
                id=str(truth.id),
                framework=truth.framework,
                control_or_clause=truth.control_or_clause,
                gap_description=truth.gap_description,
                citation_ids=[citation_id],
            )
        )
    return AssessmentReport(
        task_id=str(task_id),
        phase=case.phase,
        status="completed",
        summary="deterministic oracle report; not model performance",
        risk_items=risks,
        compliance_gaps=gaps,
        sources=sources,
    )


@pytest.mark.asyncio
async def test_six_phase_runner_reproduces_unapproved_oracle_baseline(tmp_path):
    cfg = RunConfig(
        run_id="six-phase-oracle",
        dataset_id="ssdlc_synthetic_v1",
        repeats=1,
        provider="fixture",
        model_id="deterministic-oracle-not-a-model",
        phase="full_ssdlc",
        skill_id="ssdlc-testing",
    )

    scorecard = await run_cases(
        CASES,
        cfg,
        input_root=DATASET,
        report_root=tmp_path,
        assessment_runner=_oracle_runner,
    )
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    assert baseline["approved"] is False
    assert baseline["baseline_kind"] == "deterministic_oracle_scorer_contract"
    assert scorecard["metrics"] == baseline["metrics"]
    assert len(scorecard["by_phase_skill"]) == 6
    assert scorecard["dataset"]["review_status"] == "not_expert_reviewed"
    markdown = (tmp_path / "six-phase-oracle" / "scorecard.md").read_text(
        encoding="utf-8"
    )
    assert "has not been expert reviewed" in markdown
    assert "not model performance" not in markdown.lower()
