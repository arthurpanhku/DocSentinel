"""OWASP Benchmark v1.2 adapter.

The adapter reads `expectedresults-1.2.csv` from a locally fetched Benchmark
checkout and yields one EvalCase per test servlet. It does not vendor or fetch
raw data by itself; use `evals/datasets/owasp_benchmark/fetch.py`.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from evals.models import EvalCase, EvalGroundTruth, EvalInput, VulnerabilityTruth

DATASET_ID = "owasp_benchmark"
DEFAULT_PHASE = "testing"
DEFAULT_SKILL_ID = "ssdlc-testing"
EXPECTED_RESULTS = "expectedresults-1.2.csv"


def to_cases(raw_dir: Path) -> Iterable[EvalCase]:
    """Convert a local OWASP Benchmark checkout into normalized EvalCase objects."""
    raw_dir = Path(raw_dir)
    expected_results = _find_expected_results(raw_dir)
    for row in _read_expected_results(expected_results):
        test_name = row["test_name"]
        source_path = _source_path(raw_dir, test_name)
        yield EvalCase(
            case_id=test_name,
            dataset_id=DATASET_ID,
            phase=DEFAULT_PHASE,
            skill_id=DEFAULT_SKILL_ID,
            inputs=[
                EvalInput(
                    path=str(source_path.relative_to(raw_dir)),
                    type="java",
                )
            ],
            ground_truth=EvalGroundTruth(
                vulnerabilities=[
                    VulnerabilityTruth(
                        cwe=_normalize_cwe(row["cwe"]),
                        label=(
                            "true_positive"
                            if row["real_vulnerability"]
                            else "false_positive"
                        ),
                        category=row["category"],
                        test_name=test_name,
                    )
                ]
            ),
            meta={
                "license": "Apache-2.0-ish; verify upstream project terms",
                "contamination_risk": "high",
                "source": "OWASP Benchmark v1.2",
                "expected_results": str(expected_results.relative_to(raw_dir)),
            },
        )


def _find_expected_results(raw_dir: Path) -> Path:
    direct = raw_dir / EXPECTED_RESULTS
    if direct.exists():
        return direct
    matches = sorted(raw_dir.glob(f"**/{EXPECTED_RESULTS}"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"{EXPECTED_RESULTS} not found under {raw_dir}")


def _read_expected_results(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            normalized = {
                _clean_header(key): (value or "").strip()
                for key, value in raw.items()
                if key is not None
            }
            test_name = normalized.get("test_name", "")
            cwe = normalized.get("cwe", "")
            category = normalized.get("category", "")
            real = normalized.get("real_vulnerability", "").lower()
            if not test_name or not cwe:
                continue
            rows.append(
                {
                    "test_name": test_name,
                    "category": category,
                    "real_vulnerability": real == "true",
                    "cwe": cwe,
                }
            )
    return rows


def _source_path(raw_dir: Path, test_name: str) -> Path:
    matches = sorted(raw_dir.glob(f"**/{test_name}.java"))
    if matches:
        return matches[0]
    return raw_dir / "src/main/java/org/owasp/benchmark/testcode" / f"{test_name}.java"


def _clean_header(value: str) -> str:
    return value.strip().lower().lstrip("#").strip().replace(" ", "_")


def _normalize_cwe(value: object) -> str:
    text = str(value).strip().upper()
    if not text:
        return ""
    return text if text.startswith("CWE-") else f"CWE-{text}"

