from evals.models import EvalCase


def test_eval_case_round_trips_plan_example():
    payload = {
        "case_id": "tmbench-0007",
        "dataset_id": "tmbench",
        "phase": "design",
        "skill_id": "ssdlc-design",
        "inputs": [{"path": "inputs/tmbench-0007.md", "type": "markdown"}],
        "ground_truth": {
            "threats": [
                {
                    "component": "api",
                    "stride": "S",
                    "description": "Missing caller authentication.",
                }
            ],
            "risk_items": [{"severity": "high", "description": "Auth gap."}],
            "compliance_gaps": [
                {
                    "framework": "GDPR",
                    "control_or_clause": "Art.32",
                    "gap_description": "Encryption evidence is missing.",
                }
            ],
            "vulnerabilities": [{"cwe": "CWE-89", "label": "true_positive"}],
        },
        "meta": {
            "license": "example",
            "contamination_risk": "high",
            "annotators": 2,
            "iaa": 0.71,
        },
    }

    case = EvalCase.model_validate(payload)
    restored = EvalCase.model_validate_json(case.model_dump_json())

    assert restored == case
    assert restored.phase == "design"
    assert restored.ground_truth.vulnerabilities[0].cwe == "CWE-89"

