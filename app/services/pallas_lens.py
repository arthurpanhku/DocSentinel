"""Explainable project governance radar for PallasGuard."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.models.governance import ControlInstance, ControlStatus, Project


def _status_value(control: ControlInstance) -> str:
    status = control.status
    return status.value if hasattr(status, "value") else str(status)


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _score_intake(project: Project) -> int:
    fields = [
        project.name,
        project.description,
        project.business_owner,
        project.risk_tier or project.risk_level,
        project.control_profile,
        project.system_type,
        project.hosting_type,
        project.data_classification,
    ]
    completed = sum(1 for value in fields if value not in (None, "", []))
    return round((completed / len(fields)) * 100)


def _evidence_items(control: ControlInstance) -> list[Any]:
    return list(getattr(control, "evidence_items", []) or [])


def _score_controls(applicable: list[ControlInstance]) -> int:
    if not applicable:
        return 0
    statuses = Counter(_status_value(control) for control in applicable)
    approved = statuses[ControlStatus.approved.value]
    reviewed = (
        statuses[ControlStatus.ai_reviewed.value]
        + statuses[ControlStatus.needs_clarification.value]
    )
    submitted = statuses[ControlStatus.evidence_submitted.value]
    return _clamp(
        round(
            ((approved * 1.0) + (reviewed * 0.7) + (submitted * 0.45))
            / len(applicable)
            * 100
        )
    )


def _score_evidence(applicable: list[ControlInstance]) -> int:
    mandatory = [control for control in applicable if control.is_mandatory]
    if not mandatory:
        return 0
    covered = sum(1 for control in mandatory if len(_evidence_items(control)) > 0)
    return round((covered / len(mandatory)) * 100)


def _score_ai_review(applicable: list[ControlInstance]) -> int:
    reviewable = [
        control
        for control in applicable
        if control.review_mode in {"ai_first", "ai_only"}
        and len(_evidence_items(control)) > 0
    ]
    if not reviewable:
        return 0
    reviewed = sum(
        1 for control in reviewable if control.ai_reviewed_at or control.ai_score
    )
    high_confidence = sum(
        1 for control in reviewable if (control.ai_confidence or 0) >= 0.75
    )
    return _clamp(
        round(((reviewed * 0.75) + (high_confidence * 0.25)) / len(reviewable) * 100)
    )


def _score_release(applicable: list[ControlInstance]) -> int:
    mandatory = [control for control in applicable if control.is_mandatory]
    if not mandatory:
        return 0
    blockers = {
        ControlStatus.pending.value,
        ControlStatus.rejected.value,
        ControlStatus.needs_clarification.value,
    }
    blocked = sum(1 for control in mandatory if _status_value(control) in blockers)
    return _clamp(round((1 - (blocked / len(mandatory))) * 100))


def build_pallas_lens(
    project: Project, controls: list[ControlInstance]
) -> dict[str, Any]:
    """Build a deterministic governance radar from project controls and evidence."""
    applicable = [control for control in controls if control.is_applicable]
    status_counts = Counter(_status_value(control) for control in controls)
    framework_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    evidence_total = 0

    for control in controls:
        framework_counts[control.framework_id]["total"] += 1
        framework_counts[control.framework_id][_status_value(control)] += 1
        if control.is_applicable:
            framework_counts[control.framework_id]["applicable"] += 1
        evidence_total += len(_evidence_items(control))

    dimensions = [
        {
            "key": "intake",
            "label": "Intake clarity",
            "score": _score_intake(project),
            "why": (
                "Project classification, ownership, and SSDLC profile are "
                "complete enough to drive routing."
            ),
        },
        {
            "key": "controls",
            "label": "Control progress",
            "score": _score_controls(applicable),
            "why": (
                "Applicable controls are moving from pending to evidence "
                "submitted, AI-reviewed, or approved."
            ),
        },
        {
            "key": "evidence",
            "label": "Evidence coverage",
            "score": _score_evidence(applicable),
            "why": (
                "Mandatory applicable controls have at least one evidence item "
                "attached."
            ),
        },
        {
            "key": "ai_review",
            "label": "AI review coverage",
            "score": _score_ai_review(applicable),
            "why": (
                "Evidence-backed controls have machine review results with "
                "usable confidence."
            ),
        },
        {
            "key": "release",
            "label": "Release readiness",
            "score": _score_release(applicable),
            "why": (
                "Mandatory controls avoid pending, rejected, or "
                "clarification-needed status."
            ),
        },
    ]

    weighted = (
        dimensions[0]["score"] * 0.15
        + dimensions[1]["score"] * 0.25
        + dimensions[2]["score"] * 0.25
        + dimensions[3]["score"] * 0.15
        + dimensions[4]["score"] * 0.20
    )
    readiness_score = _clamp(round(weighted))

    blockers = [
        control
        for control in applicable
        if control.is_mandatory
        and _status_value(control)
        in {
            ControlStatus.pending.value,
            ControlStatus.rejected.value,
            ControlStatus.needs_clarification.value,
        }
    ]
    no_evidence = [
        control
        for control in applicable
        if control.is_mandatory and len(_evidence_items(control)) == 0
    ]
    low_confidence = [
        control
        for control in applicable
        if control.ai_score and (control.ai_confidence or 0) < 0.65
    ]

    next_actions: list[dict[str, Any]] = []
    for control in blockers[:4]:
        next_actions.append(
            {
                "priority": "high",
                "control_id": control.control_id,
                "title": control.title,
                "action": "Resolve mandatory control blocker",
                "reason": (
                    f"{control.control_id} is "
                    f"{_status_value(control).replace('_', ' ')}."
                ),
            }
        )
    for control in no_evidence[:4]:
        if any(item.get("control_id") == control.control_id for item in next_actions):
            continue
        expected = list(control.expected_evidence or [])
        next_actions.append(
            {
                "priority": "medium",
                "control_id": control.control_id,
                "title": control.title,
                "action": "Attach expected evidence",
                "reason": expected[0]
                if expected
                else "No evidence has been attached yet.",
            }
        )
    for control in low_confidence[:3]:
        if any(item.get("control_id") == control.control_id for item in next_actions):
            continue
        next_actions.append(
            {
                "priority": "medium",
                "control_id": control.control_id,
                "title": control.title,
                "action": "Request human review",
                "reason": f"AI confidence is {control.ai_confidence:.0%}.",
            }
        )

    if not controls:
        next_actions.append(
            {
                "priority": "high",
                "control_id": None,
                "title": "Generate project controls",
                "action": "Run control generation",
                "reason": (
                    "Pallas Lens needs generated controls to build a project "
                    "governance radar."
                ),
            }
        )

    if readiness_score >= 85:
        posture = "release-ready"
        summary = (
            "The project has strong evidence coverage and few governance blockers."
        )
    elif readiness_score >= 60:
        posture = "review-needed"
        summary = (
            "The project is progressing, but several controls still need "
            "evidence or review."
        )
    else:
        posture = "attention-needed"
        summary = "The project needs focused governance work before security sign-off."

    return {
        "project_id": str(project.id),
        "readiness_score": readiness_score,
        "posture": posture,
        "summary": summary,
        "dimensions": dimensions,
        "control_totals": {
            "total": len(controls),
            "applicable": len(applicable),
            "mandatory_applicable": sum(
                1 for control in applicable if control.is_mandatory
            ),
            "evidence_items": evidence_total,
        },
        "status_counts": dict(status_counts),
        "frameworks": {
            key: dict(value) for key, value in sorted(framework_counts.items())
        },
        "next_actions": next_actions[:6],
    }
