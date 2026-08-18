import json
import re
import shutil
from pathlib import Path

import pytest

from evals.adapters.ssdlc_synthetic import to_cases

DATASET = Path(__file__).parents[1] / "datasets" / "ssdlc_synthetic_v1"


def test_adapter_loads_exactly_one_case_for_each_ssdlc_phase():
    cases = list(to_cases(DATASET))

    assert [case.phase for case in cases] == [
        "requirements",
        "design",
        "development",
        "testing",
        "deployment",
        "operations",
    ]
    assert all(len(case.ground_truth.risk_items) == 2 for case in cases)
    assert all(len(case.ground_truth.compliance_gaps) == 2 for case in cases)
    assert all(case.meta["review_status"] == "not_expert_reviewed" for case in cases)


def test_adapter_rejects_modified_ground_truth(tmp_path):
    copied = tmp_path / "dataset"
    shutil.copytree(DATASET, copied)
    with (copied / "cases.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("\n")

    with pytest.raises(ValueError, match="Checksum mismatch for cases.jsonl"):
        list(to_cases(copied))


def test_manifest_declares_only_synthetic_non_expert_reviewed_data():
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["provenance"] == "fully_synthetic"
    assert manifest["review_status"] == "not_expert_reviewed"
    assert manifest["contains_real_personal_data"] is False
    assert manifest["contains_third_party_content"] is False


def test_committed_synthetic_inputs_have_no_obvious_secret_or_contact_markers():
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((DATASET / "inputs").glob("*.md"))
    )

    assert "-----BEGIN" not in text
    assert not re.search(r"\bAKIA[0-9A-Z]{16}\b", text)
    assert not re.search(r"(?i)\b(?:api[_-]?key|password)\s*[:=]\s*['\"][^'\"]+", text)
    assert not re.search(
        r"\b[A-Z0-9._%+-]+@(?![^\s]*\.test\b)[A-Z0-9.-]+\.[A-Z]{2,}\b",
        text,
        re.I,
    )
