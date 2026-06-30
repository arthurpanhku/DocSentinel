from __future__ import annotations

# ruff: noqa: B008
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.control_generator import resolve_control_set
from app.services.light_rag import chunks_to_citations, search_knowledge
from app.services.policy_pack import (
    active_policy_pack_summary,
    list_overlay_packs,
    list_policy_packs,
    load_overlay_pack,
)
from app.services.schema_service import list_schemas, load_schema

from .utils import ok

router = APIRouter(tags=["governance-schemas"])

_SIGNAL_HINTS: dict[str, list[str]] = {
    "identity": ["access", "user", "admin", "identity", "auth", "mfa", "login"],
    "data": ["data", "personal", "privacy", "confidential", "encryption"],
    "logging": ["log", "monitor", "audit", "incident", "retention"],
    "hosting": ["hosting", "cloud", "saas", "third party", "outsourced"],
    "testing": ["release", "source code", "vulnerability", "test", "scan"],
    "special": ["ai", "genai", "iot", "rpa", "mobile"],
}


def _text(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, list):
            parts.extend(str(item) for item in value if item)
        elif value:
            parts.append(str(value))
    return " ".join(parts).lower()


def _signals_for_field(field: dict[str, Any]) -> list[str]:
    haystack = _text(
        field.get("key"),
        field.get("label"),
        field.get("group"),
        field.get("question_details"),
        field.get("decision_scope"),
        field.get("options"),
    )
    signals = [
        signal
        for signal, words in _SIGNAL_HINTS.items()
        if any(word in haystack for word in words)
    ]
    return sorted(set(signals or ["testing"]))


def _profile_graph(
    profile: str,
    fields: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> dict[str, Any]:
    control_by_id = {control.get("control_id"): control for control in controls}
    field_edges: list[dict[str, Any]] = []
    signal_counts = {signal: 0 for signal in _SIGNAL_HINTS}
    signal_control_ids: dict[str, set[str]] = {
        signal: set() for signal in _SIGNAL_HINTS
    }
    for field in fields:
        signals = _signals_for_field(field)
        for signal in signals:
            signal_counts[signal] += 1
        direct_ids = [
            control_id
            for control_id in field.get("maps_to_controls", [])
            if control_id in control_by_id
        ]
        control_ids = direct_ids[:10]
        for signal in signals:
            signal_control_ids[signal].update(control_ids)
        field_edges.append(
            {
                "field_key": field.get("key"),
                "field_label": field.get("label") or field.get("key"),
                "signals": signals,
                "control_ids": control_ids,
                "direct": bool(direct_ids),
            }
        )
    rag_chunks = search_knowledge(
        "SSDLC ontology intake question controls framework evidence",
        top_k=6,
    )
    return {
        "profile": profile,
        "field_count": len(fields),
        "control_count": len(controls),
        "signals": [
            {
                "id": signal,
                "field_count": signal_counts[signal],
                "control_count": len(signal_control_ids[signal]),
            }
            for signal in _SIGNAL_HINTS
        ],
        "field_edges": field_edges,
        "citations": chunks_to_citations(rag_chunks),
    }


@router.get("/policy-packs")
async def list_available_policy_packs() -> dict[str, Any]:
    base_packs = list_policy_packs()
    overlays = list_overlay_packs()
    all_packs = [{**pack, "type": "base"} for pack in base_packs] + [
        {**pack, "type": "overlay"} for pack in overlays
    ]
    return ok(
        {
            "active": active_policy_pack_summary(),
            "available": base_packs,
            "overlays": overlays,
            "all": all_packs,
        },
        {"count": len(all_packs)},
    )


@router.get("/schemas")
async def list_node_schemas() -> dict[str, Any]:
    return ok(list_schemas(), {"policy_pack": active_policy_pack_summary()})


@router.get("/schemas/{node_key}")
async def get_node_schema(node_key: str) -> dict[str, Any]:
    try:
        schema = load_schema(node_key)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ok(schema)


@router.get("/ontology-graph")
async def get_ontology_graph() -> dict[str, Any]:
    fields = load_schema("phase1_intake").get("fields", [])
    controls = load_schema("phase5_control_verify").get("controls", [])
    return ok(
        {
            "profiles": {
                "full": _profile_graph("full", fields, controls),
                "essential": _profile_graph("essential", fields, controls),
            },
            "note": (
                "Relationships are derived from policy-pack schemas and local "
                "Light RAG citations."
            ),
        },
        {"policy_pack": active_policy_pack_summary()},
    )


@router.get("/framework-questionnaire")
async def get_framework_questionnaire(
    framework_ids: list[str] = Query(default=[]),
) -> dict[str, Any]:
    base_fields = load_schema("phase1_intake").get("fields", [])
    available = list_overlay_packs()
    selected_ids = framework_ids or [item["id"] for item in available]
    frameworks: list[dict[str, Any]] = []
    for framework in available:
        framework_id = framework["id"]
        if framework_id not in selected_ids:
            continue
        try:
            overlay = load_overlay_pack(framework_id)
        except FileNotFoundError:
            continue
        required = set(
            str(item) for item in overlay.manifest.get("required_questions") or []
        )
        questions = [
            field for field in base_fields if str(field.get("key")) in required
        ]
        controls = [
            {
                "control_id": control.control_id,
                "family": control.family,
                "title": control.title,
                "normalized_requirement": control.normalized_requirement,
                "expected_evidence": control.expected_evidence,
                "review_focus": control.review_focus,
                "source_frameworks": control.source_frameworks,
            }
            for control in resolve_control_set([framework_id])
            if framework_id in control.source_frameworks
        ]
        frameworks.append({**framework, "questions": questions, "controls": controls})
    return ok(
        {"base_questions": base_fields, "frameworks": frameworks},
        {"policy_pack": active_policy_pack_summary()},
    )
