"""Export machine-readable API and report contracts from application models."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app.models.assessment import AssessmentReport  # noqa: E402

OPENAPI_PATH = ROOT / "docs" / "openapi.json"
REPORT_SCHEMA_PATH = ROOT / "docs" / "schemas" / "assessment-report.json"


def _render(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _contracts() -> dict[Path, str]:
    return {
        OPENAPI_PATH: _render(app.openapi()),
        REPORT_SCHEMA_PATH: _render(AssessmentReport.model_json_schema()),
    }


def export_contracts(check: bool) -> int:
    stale: list[Path] = []
    for path, content in _contracts().items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    if stale:
        joined = ", ".join(str(path.relative_to(ROOT)) for path in stale)
        print(f"Generated contracts are stale: {joined}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated contracts differ from committed files.",
    )
    args = parser.parse_args()
    return export_contracts(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
