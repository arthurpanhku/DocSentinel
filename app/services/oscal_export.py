"""OSCAL-style export helpers for governance controls and evidence.

The payloads intentionally use plain dictionaries so they stay easy to serve
through FastAPI and to evolve as DocSentinel adopts stricter OSCAL validation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

from sqlmodel import Session, select

from app.models.governance import ControlEvidenceItem, ControlInstance, Project
from app.services.control_generator import ControlDef, resolve_control_set
from app.services.policy_pack import active_policy_pack_summary

OSCAL_VERSION = "1.1.2"
OPENCRE_NS = "https://opencre.org/"


def _stable_uuid(*parts: Any) -> str:
    text = ":".join(str(part) for part in parts if part is not None)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"docsentinel:{text}"))


def _iso(value: datetime | None) -> str:
    dt = value or datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _text(value: str | None, limit: int = 500) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}..."


def _opencre_search_url(framework_id: str, control_id: str) -> str:
    query = quote_plus(f"{framework_id} {control_id}")
    return f"{OPENCRE_NS}?search={query}"


def _control_props(
    *,
    control_id: str,
    framework_id: str,
    source: str = "docsentinel",
) -> list[dict[str, str]]:
    return [
        {"name": "source", "value": source},
        {"name": "framework-id", "value": framework_id},
        {"name": "opencre-search", "ns": OPENCRE_NS, "value": control_id},
    ]


def _control_links(framework_id: str, control_id: str) -> list[dict[str, str]]:
    return [
        {
            "rel": "related",
            "href": _opencre_search_url(framework_id, control_id),
            "text": "OpenCRE requirement search",
        }
    ]


def _control_part(name: str, prose: str | list[str] | None) -> dict[str, Any] | None:
    if isinstance(prose, list):
        prose = "\n".join(f"- {item}" for item in prose if item)
    prose = str(prose or "").strip()
    if not prose:
        return None
    return {"name": name, "prose": prose}


def _catalog_control(control: ControlDef) -> dict[str, Any]:
    framework_id = (control.source_frameworks or ["generic-ssdlc"])[0]
    parts = [
        part
        for part in (
            _control_part("statement", control.normalized_requirement),
            _control_part("expected-evidence", control.expected_evidence),
            _control_part("review-focus", control.review_focus),
        )
        if part is not None
    ]
    props = _control_props(
        control_id=control.control_id,
        framework_id=framework_id,
        source="docsentinel-policy-pack",
    )
    for source_framework in control.source_frameworks:
        props.append({"name": "source-framework", "value": source_framework})
    return {
        "id": control.control_id,
        "title": control.title,
        "props": props,
        "links": _control_links(framework_id, control.control_id),
        "parts": parts,
    }


def build_oscal_catalog(
    framework_ids: list[str] | None = None,
    *,
    pack_id: str | None = None,
) -> dict[str, Any]:
    """Build an OSCAL catalog-like export for resolved DocSentinel controls."""

    selected_frameworks = framework_ids or []
    controls = resolve_control_set(selected_frameworks, pack_id=pack_id)
    active_pack = active_policy_pack_summary()

    groups: dict[str, list[dict[str, Any]]] = {}
    for control in controls:
        groups.setdefault(control.family or "General", []).append(
            _catalog_control(control)
        )

    return {
        "catalog": {
            "uuid": _stable_uuid(
                "catalog",
                active_pack.get("id"),
                ",".join(sorted(selected_frameworks)),
            ),
            "metadata": {
                "title": "DocSentinel Governance Control Catalog",
                "last-modified": _iso(None),
                "version": str(active_pack.get("version") or "1.0.0"),
                "oscal-version": OSCAL_VERSION,
                "props": [
                    {"name": "policy-pack-id", "value": str(active_pack.get("id"))},
                    {
                        "name": "selected-frameworks",
                        "value": ",".join(selected_frameworks) or "base",
                    },
                ],
            },
            "groups": [
                {
                    "id": family.lower().replace(" ", "-"),
                    "title": family,
                    "controls": sorted(items, key=lambda item: item["id"]),
                }
                for family, items in sorted(groups.items())
            ],
        }
    }


def _status_state(status: str, applicable: bool) -> str:
    if not applicable or status == "not_applicable":
        return "not-applicable"
    if status == "approved":
        return "satisfied"
    if status in {"rejected", "needs_clarification"}:
        return "not-satisfied"
    return "under-review"


def _evidence_href(item: ControlEvidenceItem) -> str:
    if item.url:
        return item.url
    if item.file_path:
        return item.file_path
    return f"#evidence-{item.id}"


def _observation(
    project: Project,
    control: ControlInstance,
    evidence: ControlEvidenceItem,
) -> dict[str, Any]:
    content = evidence.content or evidence.url or evidence.file_path
    return {
        "uuid": _stable_uuid("observation", project.id, control.id, evidence.id),
        "title": f"Evidence for {control.control_id}",
        "description": _text(content, 500) or "Evidence item captured in DocSentinel.",
        "methods": ["EXAMINE"],
        "collected": _iso(evidence.submitted_at),
        "props": [
            {"name": "control-id", "value": control.control_id},
            {"name": "framework-id", "value": control.framework_id},
            {"name": "evidence-type", "value": evidence.evidence_type},
        ],
        "subjects": [
            {
                "uuid": _stable_uuid("subject", project.id, control.id),
                "type": "component",
                "title": project.name,
            }
        ],
        "relevant-evidence": [
            {
                "href": _evidence_href(evidence),
                "description": _text(content, 240) or "DocSentinel evidence item",
            }
        ],
    }


def _finding(control: ControlInstance, evidence_count: int) -> dict[str, Any]:
    state = _status_state(control.status, control.is_applicable)
    remarks = (
        control.human_notes or control.ai_rationale or control.applicability_rationale
    )
    return {
        "uuid": _stable_uuid("finding", control.project_id, control.id),
        "title": f"{control.control_id}: {control.title}",
        "description": control.normalized_requirement,
        "target": {
            "type": "objective-id",
            "target-id": control.control_id,
            "status": {
                "state": state,
                "reason": control.status,
            },
        },
        "props": [
            {"name": "framework-id", "value": control.framework_id},
            {"name": "framework-citation", "value": control.framework_citation or ""},
            {"name": "evidence-count", "value": str(evidence_count)},
            {"name": "review-mode", "value": control.review_mode},
        ],
        "links": _control_links(control.framework_id, control.control_id),
        "remarks": _text(remarks, 1000),
    }


def build_project_assessment_results(
    project: Project,
    session: Session,
) -> dict[str, Any]:
    """Export project controls, evidence, and findings as OSCAL assessment results."""

    controls = session.exec(
        select(ControlInstance)
        .where(ControlInstance.project_id == project.id)
        .order_by(ControlInstance.framework_id, ControlInstance.control_id)
    ).all()
    evidence_by_control: dict[uuid.UUID, list[ControlEvidenceItem]] = {}
    for control in controls:
        if control.id is None:
            continue
        evidence_by_control[control.id] = session.exec(
            select(ControlEvidenceItem).where(
                ControlEvidenceItem.control_instance_id == control.id
            )
        ).all()

    observations = [
        _observation(project, control, evidence)
        for control in controls
        for evidence in evidence_by_control.get(control.id, [])
    ]
    findings = [
        _finding(control, len(evidence_by_control.get(control.id, [])))
        for control in controls
    ]
    latest = max(
        [project.updated_at, *[control.updated_at for control in controls]],
        default=datetime.now(UTC),
    )
    org_name = project.organization or "DocSentinel user organization"
    result_uuid = _stable_uuid("assessment-result", project.id)

    return {
        "assessment-results": {
            "uuid": _stable_uuid("assessment-results", project.id),
            "metadata": {
                "title": f"DocSentinel assessment results: {project.name}",
                "last-modified": _iso(latest),
                "version": "1.0.0",
                "oscal-version": OSCAL_VERSION,
                "parties": [
                    {
                        "uuid": _stable_uuid("party", project.id, org_name),
                        "type": "organization",
                        "name": org_name,
                    }
                ],
                "props": [
                    {"name": "project-id", "value": str(project.id)},
                    {"name": "project-status", "value": project.status},
                    {
                        "name": "compliance-frameworks",
                        "value": ",".join(project.compliance_frameworks or []),
                    },
                ],
            },
            "import-ap": {
                "href": "#docsentinel-active-controls",
                "remarks": "Controls are exported from DocSentinel policy packs.",
            },
            "results": [
                {
                    "uuid": result_uuid,
                    "title": f"Governance assessment for {project.name}",
                    "description": project.description
                    or "DocSentinel governance assessment export.",
                    "start": _iso(project.created_at),
                    "end": _iso(latest),
                    "reviewed-controls": {
                        "control-selections": [
                            {
                                "description": "DocSentinel generated controls",
                                "include-controls": [
                                    {
                                        "control-id": control.control_id,
                                        "props": _control_props(
                                            control_id=control.control_id,
                                            framework_id=control.framework_id,
                                        ),
                                        "links": _control_links(
                                            control.framework_id,
                                            control.control_id,
                                        ),
                                    }
                                    for control in controls
                                ],
                            }
                        ]
                    },
                    "observations": observations,
                    "findings": findings,
                }
            ],
        }
    }
