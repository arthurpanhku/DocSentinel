"""Generate governance control instances from policy-pack schemas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import delete
from sqlmodel import Session, select

from app.models.governance import (
    ControlInstance,
    ControlStatus,
    OrgFrameworkConfig,
    Project,
)
from app.services.policy_pack import load_overlay_pack, resolve_project_frameworks
from app.services.schema_service import load_schema


@dataclass
class ControlDef:
    control_id: str
    family: str
    title: str
    normalized_requirement: str
    expected_evidence: list[str] = field(default_factory=list)
    review_focus: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    source_frameworks: list[str] = field(default_factory=list)
    framework_citations: dict[str, str] = field(default_factory=dict)
    load_condition: str | None = None
    ai_only: bool = False
    is_mandatory: bool = True


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    if isinstance(value, tuple | set):
        return [str(v) for v in value if str(v)]
    text = str(value).strip()
    if not text:
        return []
    inline = re.findall(r"`([^`]*)`", text)
    return inline if inline else [text]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "yes", "1", "y"}


def _control_from_dict(
    raw: dict[str, Any],
    *,
    source_framework: str = "generic-ssdlc",
) -> ControlDef:
    cid = str(raw.get("control_id") or "").strip()
    return ControlDef(
        control_id=cid,
        family=str(raw.get("family") or "General"),
        title=str(raw.get("title") or cid),
        normalized_requirement=str(
            raw.get("normalized_requirement") or raw.get("requirement") or ""
        ),
        expected_evidence=_as_list(raw.get("expected_evidence")),
        review_focus=_as_list(raw.get("review_focus")),
        frameworks=_as_list(raw.get("frameworks")),
        source_frameworks=[source_framework],
        load_condition=str(raw.get("load_condition") or "").strip() or None,
        ai_only=_bool(raw.get("ai_only")),
        is_mandatory=not _bool(raw.get("optional")),
    )


def _merge_control(existing: ControlDef, incoming: ControlDef) -> ControlDef:
    for attr in (
        "expected_evidence",
        "review_focus",
        "frameworks",
        "source_frameworks",
    ):
        target = getattr(existing, attr)
        for item in getattr(incoming, attr):
            if item not in target:
                target.append(item)
    existing.is_mandatory = existing.is_mandatory or incoming.is_mandatory
    existing.ai_only = existing.ai_only or incoming.ai_only
    return existing


def _load_base_controls() -> dict[str, ControlDef]:
    controls: dict[str, ControlDef] = {}
    for schema_key in (
        "phase5_control_verify",
        "phase5_control_verify_ai",
        "phase5_control_verify_supplychain",
    ):
        try:
            parsed = load_schema(schema_key)
        except Exception:
            continue
        for raw in parsed.get("controls") or []:
            control = _control_from_dict(raw)
            if not control.control_id:
                continue
            if control.control_id in controls:
                _merge_control(controls[control.control_id], control)
            else:
                controls[control.control_id] = control
    return controls


def _overlay_stub(
    control_id: str,
    framework_id: str,
    citation: str | None = None,
) -> ControlDef:
    title = control_id.replace("-", " ")
    return ControlDef(
        control_id=control_id,
        family="Framework Specific",
        title=title,
        normalized_requirement=citation or f"Framework-specific control {control_id}.",
        expected_evidence=[
            "Evidence demonstrating the framework-specific requirement is met."
        ],
        review_focus=[
            "Confirm the submitted evidence satisfies the cited framework obligation."
        ],
        source_frameworks=[framework_id],
        framework_citations={framework_id: citation or ""},
    )


def resolve_control_set(
    framework_ids: list[str],
    pack_id: str | None = None,
) -> list[ControlDef]:
    controls = _load_base_controls()
    merged = resolve_project_frameworks(framework_ids, pack_id=pack_id)

    for fid in framework_ids:
        try:
            overlay = load_overlay_pack(fid)
        except FileNotFoundError:
            continue

        citations = overlay.citations
        mappings = dict(overlay.manifest.get("control_mappings") or {})
        for control_id, citation in mappings.items():
            control = controls.get(control_id)
            if control is None:
                control = _overlay_stub(control_id, fid, str(citation))
                controls[control_id] = control
            if fid not in control.source_frameworks:
                control.source_frameworks.append(fid)
            control.framework_citations[fid] = str(citation)

        for phase_cfg in overlay.phases.values():
            if not isinstance(phase_cfg, dict):
                continue
            for control_id in phase_cfg.get("additional_controls") or []:
                cid = str(control_id).strip()
                if not cid:
                    continue
                incoming = _overlay_stub(cid, fid, citations.get(cid))
                if cid in controls:
                    _merge_control(controls[cid], incoming)
                else:
                    controls[cid] = incoming

    for control_id, citation in merged.citations.items():
        if control_id in controls:
            controls[control_id].framework_citations.setdefault("overlay", citation)

    return sorted(controls.values(), key=lambda c: (c.family, c.control_id))


def _norm(value: Any) -> str:
    if isinstance(value, list | tuple | set):
        return " ".join(_norm(v) for v in value)
    return str(value or "").strip().lower()


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value) in {"true", "yes", "y", "1", "是"}


def _contains(value: Any, token: str) -> bool:
    return token.lower() in _norm(value)


def _condition_applies(
    condition: str | None,
    intake_payload: dict[str, Any],
) -> tuple[bool, str]:
    if not condition:
        return True, "No load condition; applicable by default."
    cond = condition.lower()
    if "involves_ai_ml" in cond and not _is_truthy(
        intake_payload.get("involves_ai_ml")
    ):
        return False, "AI/ML condition is not met."
    if "ai_eu_risk_class" in cond:
        risk = _norm(
            intake_payload.get("ai_eu_risk_class")
            or intake_payload.get("ai_risk_class")
        )
        if "high" in cond and risk not in {"high", "unacceptable"}:
            return False, "High-risk AI condition is not met."
    if "eu in" in cond and not _contains(intake_payload.get("geographic_scope"), "eu"):
        return False, "EU geographic scope condition is not met."
    return True, f"Load condition matched: {condition}"


def check_applicability(
    control: ControlDef,
    intake_payload: dict[str, Any] | None,
    project: Any,
) -> tuple[bool, str]:
    payload = dict(intake_payload or {})
    payload.setdefault("involves_ai_ml", getattr(project, "involves_ai_ml", None))
    payload.setdefault("ai_risk_class", getattr(project, "ai_risk_class", None))
    payload.setdefault(
        "data_classification",
        getattr(project, "data_classification", None),
    )
    payload.setdefault("hosting_model", getattr(project, "hosting_type", None))
    payload.setdefault("system_type", getattr(project, "system_type", None))

    condition_ok, condition_reason = _condition_applies(
        control.load_condition,
        payload,
    )
    if not condition_ok:
        return False, condition_reason
    if control.control_id.startswith("AI-") and not _is_truthy(
        payload.get("involves_ai_ml")
    ):
        return False, "AI-specific controls apply only when the project involves AI/ML."
    if any(
        fid.startswith("eu-") for fid in control.source_frameworks
    ) and not _contains(
        payload.get("geographic_scope"),
        "eu",
    ):
        return False, "EU overlay control requires EU geographic scope."
    if any(
        fid.startswith("china") for fid in control.source_frameworks
    ) and not _contains(
        payload.get("geographic_scope"),
        "cn",
    ):
        return False, "China overlay control requires CN geographic scope."
    if any(
        fid.startswith("singapore") for fid in control.source_frameworks
    ) and not _contains(
        payload.get("geographic_scope"),
        "sg",
    ):
        return False, "Singapore overlay control requires SG geographic scope."
    return True, condition_reason


def assign_review_mode(
    control: ControlDef,
    project_review_mode: str | None,
    org_config: OrgFrameworkConfig | None,
) -> str:
    if control.control_id in {"AI-GOV-02", "AI-GOV-03", "EUAI-CA-01"}:
        return "human_only"
    if org_config and org_config.require_human_for_high_risk_ai and control.ai_only:
        return "human_only"
    if project_review_mode:
        return project_review_mode
    if org_config:
        return org_config.default_review_mode
    return "ai_first"


def get_org_framework_config(session: Session) -> OrgFrameworkConfig | None:
    return session.exec(
        select(OrgFrameworkConfig).order_by(OrgFrameworkConfig.updated_at.desc())
    ).first()


def generate_controls_for_project(
    project: Project,
    intake_payload: dict[str, Any] | None,
    framework_ids: list[str],
    review_mode: str,
    session: Session,
    regenerate: bool = False,
) -> dict[str, Any]:
    if regenerate:
        session.exec(
            delete(ControlInstance).where(ControlInstance.project_id == project.id)
        )
        session.flush()

    org_config = get_org_framework_config(session)
    control_defs = resolve_control_set(
        framework_ids or project.compliance_frameworks or []
    )
    existing = {
        (ci.control_id, ci.framework_id): ci
        for ci in session.exec(
            select(ControlInstance).where(ControlInstance.project_id == project.id)
        ).all()
    }

    newly_generated = 0
    updated = 0
    by_framework: dict[str, int] = {}

    for control in control_defs:
        framework_sources = control.source_frameworks or ["generic-ssdlc"]
        for framework_id in framework_sources:
            is_applicable, rationale = check_applicability(
                control,
                intake_payload,
                project,
            )
            key = (control.control_id, framework_id)
            status = (
                ControlStatus.pending.value
                if is_applicable
                else ControlStatus.not_applicable.value
            )
            citation = control.framework_citations.get(
                framework_id
            ) or control.framework_citations.get("overlay")
            instance = existing.get(key)
            if instance is None:
                instance = ControlInstance(
                    project_id=project.id,
                    control_id=control.control_id,
                    framework_id=framework_id,
                    title=control.title,
                    normalized_requirement=control.normalized_requirement,
                )
                session.add(instance)
                newly_generated += 1
            else:
                updated += 1

            instance.framework_citation = citation
            instance.title = control.title
            instance.normalized_requirement = control.normalized_requirement
            instance.expected_evidence = control.expected_evidence
            instance.review_focus = control.review_focus
            instance.is_applicable = is_applicable
            instance.applicability_rationale = rationale
            instance.is_mandatory = control.is_mandatory
            instance.review_mode = assign_review_mode(control, review_mode, org_config)
            if instance.status in {
                ControlStatus.pending.value,
                ControlStatus.not_applicable.value,
            }:
                instance.status = status
            by_framework[framework_id] = by_framework.get(framework_id, 0) + 1

    project.compliance_frameworks = framework_ids
    project.review_mode = review_mode
    project.framework_ids_locked = True
    session.add(project)
    session.commit()

    controls = session.exec(
        select(ControlInstance).where(ControlInstance.project_id == project.id)
    ).all()
    total = len(controls)
    applicable = sum(1 for control in controls if control.is_applicable)
    return {
        "total_controls": total,
        "applicable_controls": applicable,
        "not_applicable_controls": total - applicable,
        "by_framework": by_framework,
        "newly_generated": newly_generated,
        "updated": updated,
    }


def summarize_controls(project_id: Any, session: Session) -> dict[str, Any]:
    controls = session.exec(
        select(ControlInstance).where(ControlInstance.project_id == project_id)
    ).all()
    status_keys = [
        "pending",
        "evidence_submitted",
        "ai_reviewed",
        "approved",
        "rejected",
        "needs_clarification",
    ]
    summary: dict[str, Any] = {
        "total": len(controls),
        "applicable": sum(1 for c in controls if c.is_applicable),
        "not_applicable": sum(1 for c in controls if not c.is_applicable),
        **{key: 0 for key in status_keys},
        "by_framework": {},
        "all_mandatory_approved": True,
    }
    for control in controls:
        status = str(control.status)
        if status in summary:
            summary[status] += 1
        fw = summary["by_framework"].setdefault(control.framework_id, {})
        fw[status] = fw.get(status, 0) + 1
        if control.is_mandatory and control.is_applicable and status != "approved":
            summary["all_mandatory_approved"] = False
    return summary
