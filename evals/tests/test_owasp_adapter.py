from pathlib import Path

from evals.adapters.owasp_benchmark import to_cases

FIXTURE = Path(__file__).parent / "fixtures" / "owasp_benchmark"


def test_owasp_adapter_reads_expected_results_fixture():
    cases = list(to_cases(FIXTURE))

    assert [case.case_id for case in cases] == [
        "BenchmarkTest00001",
        "BenchmarkTest00002",
    ]
    assert cases[0].phase == "testing"
    assert cases[0].skill_id == "ssdlc-testing"
    assert cases[0].inputs[0].type == "java"
    assert cases[0].ground_truth.vulnerabilities[0].cwe == "CWE-22"
    assert cases[0].ground_truth.vulnerabilities[0].label == "true_positive"
    assert cases[1].ground_truth.vulnerabilities[0].cwe == "CWE-89"
    assert cases[1].ground_truth.vulnerabilities[0].label == "false_positive"

