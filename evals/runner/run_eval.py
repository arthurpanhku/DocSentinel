"""M1 evaluation runner.

Runs normalized cases through DocSentinel's AssessmentService directly and
produces machine-readable and human-readable scorecards.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.models.assessment import AssessmentReport
from app.services.assessment_service import AssessmentRunner, AssessmentService
from evals.models import EvalCase, RunConfig
from evals.runner.parse import parse_inputs
from evals.scoring.scorers.triage import (
    TriageRecord,
    record_from_report,
    score_records,
)

EVALS_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = EVALS_DIR / "registry.yaml"
MATRIX_PATH = EVALS_DIR / "configs" / "matrix.yaml"


async def run_case(
    case: EvalCase,
    cfg: RunConfig,
    *,
    input_root: Path,
    assessment_runner: AssessmentRunner | None = None,
) -> AssessmentReport:
    """Run one case through AssessmentService and return its report."""
    docs = parse_inputs(case, input_root)
    svc = AssessmentService()
    if assessment_runner is None:
        created = await svc.submit(
            docs,
            phase=case.phase,
            skill_id=case.skill_id,
            collaborative_mode=cfg.collaborative,
            source="eval",
        )
    else:
        created = await svc.submit(
            docs,
            phase=case.phase,
            skill_id=case.skill_id,
            collaborative_mode=cfg.collaborative,
            source="eval",
            runner=assessment_runner,
        )
    result = await svc.wait_for_terminal(
        str(created.task_id),
        timeout_seconds=cfg.timeout_seconds,
    )
    if result.report is None:
        raise RuntimeError(
            f"Assessment for {case.case_id} produced no report: {result.error_message}"
        )
    return result.report


async def run_cases(
    cases: Iterable[EvalCase],
    cfg: RunConfig,
    *,
    input_root: Path,
    report_root: Path | None = None,
    assessment_runner: AssessmentRunner | None = None,
) -> dict[str, Any]:
    """Run cases, score SAST triage, and write scorecard files."""
    selected = list(cases)
    if cfg.limit is not None:
        selected = selected[: cfg.limit]

    records: list[TriageRecord] = []
    for case in selected:
        for repeat in range(cfg.repeats):
            report = await run_case(
                case,
                cfg,
                input_root=input_root,
                assessment_runner=assessment_runner,
            )
            records.append(record_from_report(case, report, repeat))

    scorecard = build_scorecard(
        records,
        cfg,
        n_cases=len(selected),
        dataset_meta=_dataset_meta(cfg.dataset_id),
    )
    write_scorecard(
        scorecard,
        (report_root or EVALS_DIR / "reports") / cfg.run_id,
    )
    return scorecard


def build_scorecard(
    records: list[TriageRecord],
    cfg: RunConfig,
    *,
    n_cases: int,
    dataset_meta: dict[str, Any],
) -> dict[str, Any]:
    metrics = score_records(records)
    phase_skill: dict[tuple[str, str], list[TriageRecord]] = {}
    for record in records:
        phase_skill.setdefault((record.phase, record.skill_id), []).append(record)

    return {
        "schema_version": "eval-scorecard-v1",
        "run_id": cfg.run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "id": cfg.dataset_id,
            "source_url": dataset_meta.get("source_url"),
            "license": dataset_meta.get("license"),
            "checksum_algorithm": dataset_meta.get("checksum_algorithm"),
            "checksum": dataset_meta.get("checksum"),
            "contamination_risk": dataset_meta.get("contamination_risk"),
        },
        "model": {
            "provider": cfg.provider,
            "model_id": cfg.model_id,
            "temperature": cfg.temperature,
        },
        "run_config": {
            "repeats": cfg.repeats,
            "timeout_seconds": cfg.timeout_seconds,
            "collaborative": cfg.collaborative,
            "phase": cfg.phase,
            "skill_id": cfg.skill_id,
            "limit": cfg.limit,
        },
        "n_cases": n_cases,
        "n_records": len(records),
        "metrics": metrics,
        "by_phase_skill": [
            {
                "phase": phase,
                "skill_id": skill_id,
                "metrics": score_records(group),
            }
            for (phase, skill_id), group in sorted(phase_skill.items())
        ],
        "cases": [
            {
                "case_id": record.case_id,
                "repeat": record.repeat,
                "cwe": record.cwe,
                "truth_label": record.truth_label,
                "predicted_positive": record.predicted_positive,
                "outcome": record.outcome,
            }
            for record in records
        ],
    }


def write_scorecard(scorecard: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scorecard.json").write_text(
        json.dumps(scorecard, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "scorecard.md").write_text(
        render_scorecard_markdown(scorecard),
        encoding="utf-8",
    )


def render_scorecard_markdown(scorecard: dict[str, Any]) -> str:
    metrics = scorecard["metrics"]
    lines = [
        f"# Eval Scorecard: {scorecard['run_id']}",
        "",
        f"- Dataset: `{scorecard['dataset']['id']}`",
        f"- Model: `{scorecard['model']['provider']}:{scorecard['model']['model_id']}`",
        f"- Temperature: `{scorecard['model']['temperature']}`",
        f"- Repeats: `{scorecard['run_config']['repeats']}`",
        f"- Contamination risk: `{scorecard['dataset']['contamination_risk']}`",
        "",
        "## Overall Triage Metrics",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
    ]
    for key in ("accuracy", "precision", "recall", "f1", "false_positive_rate"):
        lines.append(f"| {key} | {metrics[key]:.4f} |")
    lines.extend(
        [
            f"| TP | {metrics['tp']} |",
            f"| FP | {metrics['fp']} |",
            f"| TN | {metrics['tn']} |",
            f"| FN | {metrics['fn']} |",
            "",
            "## By Skill / Phase",
            "",
            "| Phase | Skill | Accuracy | Precision | Recall | F1 | FP Rate |",
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in scorecard["by_phase_skill"]:
        group = item["metrics"]
        lines.append(
            "| {phase} | {skill} | {accuracy:.4f} | {precision:.4f} | "
            "{recall:.4f} | {f1:.4f} | {fp_rate:.4f} |".format(
                phase=item["phase"],
                skill=item["skill_id"],
                accuracy=group["accuracy"],
                precision=group["precision"],
                recall=group["recall"],
                f1=group["f1"],
                fp_rate=group["false_positive_rate"],
            )
        )
    lines.extend(
        [
            "",
            "M1 uses hard-key CWE matching for OWASP Benchmark and no LLM judge.",
            "",
        ]
    )
    return "\n".join(lines)


def load_adapter(dataset_id: str):
    dataset = _dataset_meta(dataset_id)
    adapter_path = dataset.get("adapter")
    if not adapter_path:
        raise ValueError(f"Dataset has no adapter configured: {dataset_id}")
    module_name, _, func_name = str(adapter_path).partition(":")
    if not module_name or not func_name:
        raise ValueError(f"Invalid adapter path for {dataset_id}: {adapter_path}")
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def load_matrix_config(dataset_id: str) -> RunConfig:
    matrix = _load_yaml(MATRIX_PATH)
    defaults = dict(matrix.get("defaults") or {})
    dataset_cfg = dict((matrix.get("datasets") or {}).get(dataset_id) or {})
    model = (matrix.get("models") or [{}])[0]
    return RunConfig(
        dataset_id=dataset_id,
        provider=str(model.get("provider") or "unknown"),
        model_id=str(model.get("model_id") or "unknown"),
        temperature=float(
            dataset_cfg.get("temperature", defaults.get("temperature", 0.0))
        ),
        repeats=int(dataset_cfg.get("repeats", defaults.get("repeats", 3))),
        timeout_seconds=int(
            dataset_cfg.get("timeout_seconds", defaults.get("timeout_seconds", 300))
        ),
        phase=dataset_cfg.get("phase", "testing"),
        skill_id=dataset_cfg.get("skill_id", "ssdlc-testing"),
    )


def _dataset_meta(dataset_id: str) -> dict[str, Any]:
    registry = _load_yaml(REGISTRY_PATH)
    datasets = registry.get("datasets") or {}
    if dataset_id not in datasets:
        raise ValueError(f"Unknown dataset: {dataset_id}")
    return dict(datasets[dataset_id])


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


async def _main_async(args: argparse.Namespace) -> None:
    cfg = load_matrix_config(args.dataset_id)
    cfg = cfg.model_copy(
        update={
            "run_id": args.run_id,
            "repeats": args.repeats or cfg.repeats,
            "limit": args.limit,
        }
    )
    adapter = load_adapter(args.dataset_id)
    cases = list(adapter(Path(args.raw_dir)))
    await run_cases(
        cases,
        cfg,
        input_root=Path(args.raw_dir),
        report_root=Path(args.report_root),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", default="owasp_benchmark")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--run-id", default="local")
    parser.add_argument("--report-root", default=str(EVALS_DIR / "reports"))
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    asyncio.run(_main_async(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
