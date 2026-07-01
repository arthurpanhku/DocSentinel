"""
Parse Markdown-driven sub-agent field/control schemas from the active policy pack.

Supported schema types:
  - field schemas    → list of FieldDef
  - control schemas  → list of ControlDef

The Markdown format is:
  ### Field: <key>        or    ### Control: <ctrl_id>
  - prop: `value`
  - list_prop:
    - `item1`
    - `item2`
"""

from __future__ import annotations

import re
from typing import Any

from app.services.policy_pack import (
    gate3_node_key_for_profile,
    list_schema_keys,
    load_policy_pack,
    resolve_node_key,
    schema_path,
)

# Regex helpers
_BACKTICK_VAL = re.compile(r"`([^`]*)`")
_PROP_LINE = re.compile(r"^-\s+(\w[\w_]*):\s*(.*)")
_LIST_ITEM = re.compile(r"^\s+-\s+(.*)")
_FIELD_HEADER = re.compile(r"^###\s+Field:\s+(\S+)")
_CONTROL_HEADER = re.compile(r"^###\s+Control:\s+(\S+)")
_SECTION_HEADER = re.compile(r"^##\s+(.+)")


def _strip_backticks(text: str) -> str:
    m = _BACKTICK_VAL.search(text)
    return m.group(1) if m else text.strip()


def _coerce(value: str) -> Any:
    """Convert string values to Python primitives."""
    v = _strip_backticks(value).strip()
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    return v


def _parse_node_meta(lines: list[str]) -> dict[str, Any]:
    """Extract top-level ## Node section key-value pairs."""
    meta: dict[str, Any] = {}
    in_node = False
    for line in lines:
        line = line.rstrip()
        m = _SECTION_HEADER.match(line)
        if m:
            in_node = m.group(1).strip() == "Node"
            continue
        if in_node:
            pm = _PROP_LINE.match(line)
            if pm:
                meta[pm.group(1)] = _coerce(pm.group(2))
    return meta


def _parse_fields(lines: list[str]) -> list[dict[str, Any]]:
    """Parse ### Field: blocks into structured dicts."""
    fields: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None

    for raw in lines:
        line = raw.rstrip()

        fh = _FIELD_HEADER.match(line)
        if fh:
            if current is not None:
                fields.append(current)
            current = {"key": fh.group(1)}
            current_list_key = None
            continue

        if current is None:
            continue

        # Detect list continuation
        li = _LIST_ITEM.match(line)
        if li and current_list_key:
            current[current_list_key].append(_coerce(li.group(1)))
            continue

        pm = _PROP_LINE.match(line)
        if pm:
            key, val = pm.group(1), pm.group(2).strip()
            if not val:
                # multi-value list follows
                current[key] = []
                current_list_key = key
            else:
                current[key] = _coerce(val)
                current_list_key = None
            continue

        # Nested source_excel sub-properties (sheet/row_ref)
        if current_list_key is None and line.strip().startswith("-") and ":" in line:
            sub = line.strip().lstrip("- ")
            k, _, v = sub.partition(":")
            k = k.strip()
            v = v.strip()
            if "source_excel" in current:
                if isinstance(current["source_excel"], dict):
                    current["source_excel"][k] = _coerce(v)
            else:
                current["source_excel"] = {k: _coerce(v)}

    if current is not None:
        fields.append(current)
    return fields


def _parse_controls(lines: list[str]) -> list[dict[str, Any]]:
    """Parse ### Control: blocks into structured dicts."""
    controls: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None

    for raw in lines:
        line = raw.rstrip()

        ch = _CONTROL_HEADER.match(line)
        if ch:
            if current is not None:
                controls.append(current)
            current = {"control_id": ch.group(1)}
            current_list_key = None
            continue

        if current is None:
            continue

        # Stop at ## sections (e.g. ## Suggested Test Flow)
        if _SECTION_HEADER.match(line):
            break

        li = _LIST_ITEM.match(line)
        if li and current_list_key:
            current[current_list_key].append(_coerce(li.group(1)))
            continue

        pm = _PROP_LINE.match(line)
        if pm:
            key, val = pm.group(1), pm.group(2).strip()
            if not val:
                current[key] = []
                current_list_key = key
            else:
                current[key] = _coerce(val)
                current_list_key = None

    if current is not None:
        controls.append(current)
    return controls


def load_schema(node_key: str) -> dict[str, Any]:
    """
    Load and parse a sub-agent schema by node_key.

    Returns:
        {
          "node_key": str,
          "meta": {gate, parent_agent, title, ...},
          "fields": [...],      # for gate1_* schemas
          "controls": [...],    # for gate3_* schemas
        }
    """
    requested_key = node_key
    node_key = resolve_node_key(node_key)
    schema_file = schema_path(node_key)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    lines = schema_file.read_text(encoding="utf-8").splitlines()
    meta = _parse_node_meta(lines)
    pack = load_policy_pack()

    result: dict[str, Any] = {
        "node_key": node_key,
        "requested_node_key": requested_key,
        "policy_pack": {
            "id": pack.id,
            "name": pack.name,
            "version": pack.version,
        },
        "meta": meta,
    }

    schema_type = str(meta.get("schema_type") or "").strip().lower()
    if node_key.startswith("gate3_scd_review") or schema_type == "controls":
        result["controls"] = _parse_controls(lines)
        result["fields"] = []
    else:
        result["fields"] = _parse_fields(lines)
        result["controls"] = []

    return result


def list_schemas() -> list[str]:
    return list_schema_keys()


def get_gate3_controls(control_profile: str = "full_ssdlc") -> list[dict[str, Any]]:
    """Return built-in Phase 5 controls by control profile."""
    node_key = gate3_node_key_for_profile(control_profile)
    return load_schema(node_key)["controls"]
