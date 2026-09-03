"""Validate that a pull request carries a reviewable, security-aware plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_SECTIONS = ("Plan", "How to Verify")
HIGH_RISK_SECTIONS = ("Security impact", "Risk and rollback")
RISK_RULES = {
    "critical": (
        ".github/workflows/",
        "alembic/",
        "app/core/deps.py",
        "app/core/security.py",
    ),
    "high": (
        "app/agent_gateway/",
        "app/api/",
        "app/services/",
        "deploy.sh",
        "Dockerfile",
        "docker-compose",
    ),
    "medium": ("app/", "frontend/", "policy_packs/"),
}
ISSUE_PATTERN = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|relates\s+to)\s+#\d+\b",
    re.IGNORECASE,
)
PLACEHOLDER_PREFIXES = (
    "describe the bounded implementation",
    "describe changes to trust boundaries",
    "state failure modes",
    "**steps to test the change**",
    "验证步骤",
)


def _section(body: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}(?:\s*\|[^\n]*)?\s*$\n(.*?)(?=^##\s|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else None


def _meaningful(content: str | None) -> bool:
    if not content or len(content) < 20:
        return False
    normalized = re.sub(r"^-\s*\[[ xX]\]\s*", "", content.strip()).lower()
    return not normalized.startswith(PLACEHOLDER_PREFIXES)


def validate_pr_plan(body: str, files: list[str]) -> list[str]:
    errors: list[str] = []
    if not ISSUE_PATTERN.search(body):
        errors.append("Link an issue with 'Fixes #N' or 'Relates to #N'.")
    for heading in REQUIRED_SECTIONS:
        content = _section(body, heading)
        if not _meaningful(content):
            errors.append(f"Section '{heading}' must contain a concrete plan.")
    if classify_risk(files) in {"high", "critical"}:
        for heading in HIGH_RISK_SECTIONS:
            content = _section(body, heading)
            if not _meaningful(content):
                errors.append(
                    f"High-risk changes require a concrete '{heading}' section."
                )
    return errors


def classify_risk(files: list[str]) -> str:
    for risk in ("critical", "high", "medium"):
        if any(
            path.startswith(prefix) for path in files for prefix in RISK_RULES[risk]
        ):
            return risk
    return "low"


def _load_event(path: Path) -> tuple[str, list[str]]:
    event = json.loads(path.read_text(encoding="utf-8"))
    body = (event.get("pull_request") or {}).get("body") or ""
    files = [item["filename"] for item in event.get("changed_files_detail", [])]
    return body, files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--files", type=Path)
    args = parser.parse_args()
    body, files = _load_event(args.event)
    if args.files:
        payload = json.loads(args.files.read_text(encoding="utf-8"))
        files = [
            item["filename"] if isinstance(item, dict) else item for item in payload
        ]
    errors = validate_pr_plan(body, files)
    print(f"Risk classification: {classify_risk(files)}")
    for error in errors:
        print(f"::error::{error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
