"""Adapter for DocSentinel's six-phase, synthetic SSDLC golden set."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from evals.models import EvalCase

DATASET_ID = "ssdlc_synthetic_v1"
CASES_FILE = "cases.jsonl"
MANIFEST_FILE = "manifest.json"
PHASES = {
    "requirements",
    "design",
    "development",
    "testing",
    "deployment",
    "operations",
}


def to_cases(raw_dir: Path) -> Iterable[EvalCase]:
    """Validate dataset integrity and yield normalized six-phase cases."""
    root = Path(raw_dir).resolve()
    manifest = _load_json(root / MANIFEST_FILE)
    _validate_manifest(root, manifest)

    seen_ids: set[str] = set()
    seen_phases: set[str] = set()
    with (root / CASES_FILE).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                case = EvalCase.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid {CASES_FILE} line {line_number}: {exc}"
                ) from exc
            _validate_case(root, case, seen_ids)
            seen_ids.add(case.case_id)
            seen_phases.add(case.phase)
            yield case

    if seen_phases != PHASES:
        missing = sorted(PHASES - seen_phases)
        extra = sorted(seen_phases - PHASES)
        raise ValueError(
            "Synthetic dataset must cover all six phases; "
            f"missing={missing}, extra={extra}"
        )
    expected_cases = int(manifest.get("n_cases") or 0)
    if len(seen_ids) != expected_cases:
        raise ValueError(
            f"Manifest declares {expected_cases} cases but {len(seen_ids)} were loaded"
        )


def _validate_case(root: Path, case: EvalCase, seen_ids: set[str]) -> None:
    if case.dataset_id != DATASET_ID:
        raise ValueError(f"Unexpected dataset_id for {case.case_id}: {case.dataset_id}")
    if case.case_id in seen_ids:
        raise ValueError(f"Duplicate case_id: {case.case_id}")
    if case.phase not in PHASES:
        raise ValueError(f"Unsupported phase for {case.case_id}: {case.phase}")
    if case.skill_id != f"ssdlc-{case.phase}":
        raise ValueError(
            f"Skill/phase mismatch for {case.case_id}: {case.skill_id} / {case.phase}"
        )
    if not case.inputs:
        raise ValueError(f"Case has no input documents: {case.case_id}")
    if not case.ground_truth.risk_items or not case.ground_truth.compliance_gaps:
        raise ValueError(f"Case has incomplete finding ground truth: {case.case_id}")
    for item in [
        *case.ground_truth.risk_items,
        *case.ground_truth.compliance_gaps,
    ]:
        if not item.id or not item.match_terms or not item.evidence_locators:
            raise ValueError(
                "Ground truth needs id, match_terms, and evidence_locators: "
                f"{case.case_id}"
            )
    for item in case.inputs:
        path = (root / item.path).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(
                f"Missing or escaping input for {case.case_id}: {item.path}"
            )


def _validate_manifest(root: Path, manifest: dict[str, Any]) -> None:
    if manifest.get("dataset_id") != DATASET_ID:
        raise ValueError(
            f"Unexpected manifest dataset_id: {manifest.get('dataset_id')}"
        )
    if manifest.get("provenance") != "fully_synthetic":
        raise ValueError(
            "Synthetic dataset manifest must declare fully_synthetic provenance"
        )
    if manifest.get("review_status") != "not_expert_reviewed":
        raise ValueError("Manifest must preserve the not_expert_reviewed boundary")
    files = manifest.get("files") or {}
    if not files:
        raise ValueError("Manifest has no file checksums")
    for relative, expected in sorted(files.items()):
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(
                f"Manifest path missing or escaping dataset root: {relative}"
            )
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(
                f"Checksum mismatch for {relative}: {actual} != {expected}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
