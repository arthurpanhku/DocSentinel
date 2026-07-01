"""Policy pack discovery and loading.

Policy packs are the boundary between the open-source workflow engine and
organization-specific SSDLC controls, schemas, prompts, and branding.

Overlay packs add compliance framework–specific controls and citations on top of
a base pack (e.g. eu-cra, nist-ssdf, owasp-samm). They live under
<packs_dir>/overlays/ and are merged at runtime per project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.config import settings

_REPO_ROOT = Path(__file__).resolve().parents[2]
# Canonical location. Kept as `policy_packs/` with a legacy `frameworks/` fallback
# so existing POLICY_PACKS_DIR overrides continue to work unchanged.
_DEFAULT_PACKS_DIR = _REPO_ROOT / "policy_packs"
_LEGACY_PACKS_DIR = _REPO_ROOT / "frameworks"


@dataclass(frozen=True)
class PolicyPack:
    id: str
    name: str
    version: str
    description: str
    root: Path
    manifest: dict[str, Any]

    @property
    def schemas(self) -> dict[str, str]:
        return dict(self.manifest.get("schemas") or {})

    @property
    def aliases(self) -> dict[str, str]:
        return dict(self.manifest.get("aliases") or {})

    @property
    def control_profiles(self) -> dict[str, str]:
        return dict(self.manifest.get("control_profiles") or {})

    @property
    def brand(self) -> dict[str, Any]:
        return dict(self.manifest.get("brand") or {})

    @property
    def phases(self) -> dict[str, Any]:
        """Optional phase-level metadata (AI-era SSDLC phases)."""
        return dict(self.manifest.get("phases") or {})


@dataclass(frozen=True)
class OverlayPack:
    """Compliance overlay that adds controls and citations to a base pack."""

    id: str
    name: str
    version: str
    description: str
    root: Path
    manifest: dict[str, Any]

    @property
    def requires_base(self) -> str:
        return str(self.manifest.get("requires_base") or "generic-ssdlc")

    @property
    def applicable_regions(self) -> list[str]:
        return list(self.manifest.get("applicable_regions") or [])

    @property
    def applicable_system_types(self) -> list[str]:
        return list(self.manifest.get("applicable_system_types") or [])

    @property
    def phases(self) -> dict[str, Any]:
        """Per-phase additions keyed by phase id."""
        return dict(self.manifest.get("phases") or {})

    @property
    def citations(self) -> dict[str, str]:
        """Maps control_id → human-readable framework citation string."""
        return dict(self.manifest.get("citations") or {})

    @property
    def label(self) -> str:
        return str(self.manifest.get("label") or self.name)

    @property
    def region_group(self) -> str:
        """UI grouping hint: US / EU / ISO / Asia / Industry."""
        return str(self.manifest.get("region_group") or "Industry")


@dataclass
class MergedControlSet:
    """Resolved control set for a project: base pack controls + overlay additions."""

    base_pack_id: str
    overlay_ids: list[str]
    # phase_id → list of additional control IDs from overlays
    overlay_controls: dict[str, list[str]] = field(default_factory=dict)
    # control_id → citation string (from overlays)
    citations: dict[str, str] = field(default_factory=dict)
    # framework_id → OverlayPack metadata
    overlay_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)


def _packs_dir() -> Path:
    configured = (settings.POLICY_PACKS_DIR or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    # Prefer policy_packs/, fall back to legacy frameworks/ if present
    if _DEFAULT_PACKS_DIR.exists():
        return _DEFAULT_PACKS_DIR
    if _LEGACY_PACKS_DIR.exists():
        return _LEGACY_PACKS_DIR
    return _DEFAULT_PACKS_DIR


def _overlays_dir() -> Path:
    configured = (getattr(settings, "POLICY_PACKS_OVERLAY_DIR", "") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return _packs_dir() / "overlays"


@lru_cache(maxsize=16)
def load_policy_pack(pack_id: str | None = None) -> PolicyPack:
    selected = (pack_id or settings.POLICY_PACK_ID or "generic-ssdlc").strip()
    root = _packs_dir() / selected
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Policy pack '{selected}' was not found at {manifest_path}. "
            "Set POLICY_PACK_ID or POLICY_PACKS_DIR to load a private pack."
        )

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    pack_id_from_manifest = str(manifest.get("id") or selected)
    if pack_id_from_manifest != selected:
        raise ValueError(
            f"Policy pack folder '{selected}' contains manifest id "
            f"'{pack_id_from_manifest}'."
        )
    return PolicyPack(
        id=pack_id_from_manifest,
        name=str(manifest.get("name") or selected),
        version=str(manifest.get("version") or "0.0.0"),
        description=str(manifest.get("description") or ""),
        root=root,
        manifest=manifest,
    )


def list_policy_packs() -> list[dict[str, str]]:
    packs: list[dict[str, str]] = []
    root = _packs_dir()
    if not root.exists():
        return packs
    for manifest_path in sorted(root.glob("*/manifest.yaml")):
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            packs.append(
                {
                    "id": str(manifest.get("id") or manifest_path.parent.name),
                    "name": str(manifest.get("name") or manifest_path.parent.name),
                    "version": str(manifest.get("version") or "0.0.0"),
                    "description": str(manifest.get("description") or ""),
                }
            )
        except Exception:
            continue
    return packs


def resolve_node_key(node_key: str, *, pack_id: str | None = None) -> str:
    pack = load_policy_pack(pack_id)
    return pack.aliases.get(node_key, node_key)


def list_schema_keys(*, pack_id: str | None = None) -> list[str]:
    pack = load_policy_pack(pack_id)
    return sorted(set(pack.schemas) | set(pack.aliases))


def schema_path(node_key: str, *, pack_id: str | None = None) -> Path:
    pack = load_policy_pack(pack_id)
    resolved = pack.aliases.get(node_key, node_key)
    relative = pack.schemas.get(resolved)
    if not relative:
        raise ValueError(
            f"Unknown node_key '{node_key}'. Known: {list_schema_keys(pack_id=pack.id)}"
        )
    path = (pack.root / relative).resolve()
    if not str(path).startswith(str(pack.root.resolve())):
        raise ValueError(f"Schema path for '{resolved}' escapes policy pack root")
    return path


def gate3_node_key_for_profile(
    control_profile: str, *, pack_id: str | None = None
) -> str:
    """Legacy helper: resolve gate3/phase5 schema key from control profile name."""
    pack = load_policy_pack(pack_id)
    profile = (control_profile or "full_ssdlc").strip().lower()
    profiles = pack.control_profiles
    if profile in profiles:
        return profiles[profile]
    # AI-era alias: phase5 schemas
    phase5_fallbacks = {
        "full_ssdlc": "phase5_control_verify",
        "essential_ssdlc": "phase5_control_verify",
    }
    return profiles.get("full_ssdlc") or phase5_fallbacks.get(
        profile, "phase5_control_verify"
    )


def phase_schema_key_for_project(
    phase_id: str,
    control_profile: str | None = None,
    *,
    pack_id: str | None = None,
) -> str:
    """Resolve the primary schema key for a given phase and control profile.

    Falls back to phase-to-schema defaults for the AI-era phase naming scheme.
    """
    pack = load_policy_pack(pack_id)
    # Check if manifest defines explicit phase → schema mappings
    phases = pack.phases
    if phase_id in phases:
        phase_cfg = phases[phase_id]
        if isinstance(phase_cfg, dict) and "schema" in phase_cfg:
            return str(phase_cfg["schema"])

    # Default mapping from phase ID to schema node_key
    _PHASE_DEFAULTS: dict[str, str] = {
        "phase1": "phase1_intake",
        "phase2": "phase2_threat_model",
        "phase3": "phase3_design_review",
        "phase4": "phase4_build_security",
        "phase5": "phase5_control_verify",
        "phase6": "phase6_release_gate",
    }
    if phase_id in _PHASE_DEFAULTS:
        return _PHASE_DEFAULTS[phase_id]

    # Legacy gate-based fallback
    if phase_id in ("gate1", "1"):
        return "phase1_intake"
    if phase_id in ("gate3", "3"):
        profile = (control_profile or "full_ssdlc").strip().lower()
        return (
            "phase5_control_verify"
            if "essential" not in profile
            else "phase5_control_verify"
        )

    return phase_id


# ── Overlay pack functions ────────────────────────────────────────────────────


@lru_cache(maxsize=32)
def load_overlay_pack(overlay_id: str) -> OverlayPack:
    """Load a compliance framework overlay pack by ID."""
    root = _overlays_dir() / overlay_id
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Overlay pack '{overlay_id}' not found at {manifest_path}."
        )
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    mid = str(manifest.get("id") or overlay_id)
    return OverlayPack(
        id=mid,
        name=str(manifest.get("name") or overlay_id),
        version=str(manifest.get("version") or "0.0.0"),
        description=str(manifest.get("description") or ""),
        root=root,
        manifest=manifest,
    )


def list_overlay_packs() -> list[dict[str, Any]]:
    """Return metadata for all available compliance framework overlay packs."""
    result: list[dict[str, Any]] = []
    overlays_dir = _overlays_dir()
    if not overlays_dir.exists():
        return result
    for manifest_path in sorted(overlays_dir.glob("*/manifest.yaml")):
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            pack_id = str(manifest.get("id") or manifest_path.parent.name)
            result.append(
                {
                    "id": pack_id,
                    "name": str(manifest.get("name") or pack_id),
                    "label": str(
                        manifest.get("label") or manifest.get("name") or pack_id
                    ),
                    "version": str(manifest.get("version") or "0.0.0"),
                    "description": str(manifest.get("description") or ""),
                    "region_group": str(manifest.get("region_group") or "Industry"),
                    "applicable_regions": list(
                        manifest.get("applicable_regions") or []
                    ),
                    "applicable_system_types": list(
                        manifest.get("applicable_system_types") or []
                    ),
                }
            )
        except Exception:
            continue
    return result


def resolve_project_frameworks(
    compliance_frameworks: list[str] | None,
    *,
    pack_id: str | None = None,
) -> MergedControlSet:
    """Merge a project's compliance framework overlays with the base pack.

    Returns a MergedControlSet containing overlay-added controls per phase
    and citation strings, ready for use in agent prompts and control seeding.
    """
    base = load_policy_pack(pack_id)
    framework_ids = [f.strip() for f in (compliance_frameworks or []) if f.strip()]

    merged = MergedControlSet(
        base_pack_id=base.id,
        overlay_ids=framework_ids,
    )

    for fid in framework_ids:
        try:
            overlay = load_overlay_pack(fid)
        except FileNotFoundError:
            continue

        # Merge citations
        merged.citations.update(overlay.citations)

        # Merge per-phase additional controls
        for phase_id, phase_cfg in overlay.phases.items():
            if not isinstance(phase_cfg, dict):
                continue
            extra_controls = list(phase_cfg.get("additional_controls") or [])
            if extra_controls:
                merged.overlay_controls.setdefault(phase_id, [])
                for ctrl in extra_controls:
                    if ctrl not in merged.overlay_controls[phase_id]:
                        merged.overlay_controls[phase_id].append(ctrl)

        # Store metadata for UI / agent context
        merged.overlay_metadata[fid] = {
            "id": overlay.id,
            "name": overlay.name,
            "label": overlay.label,
            "version": overlay.version,
            "region_group": overlay.region_group,
            "applicable_regions": overlay.applicable_regions,
        }

    return merged


def active_policy_pack_summary() -> dict[str, Any]:
    pack = load_policy_pack()
    return {
        "id": pack.id,
        "name": pack.name,
        "version": pack.version,
        "description": pack.description,
        "schemas": list_schema_keys(pack_id=pack.id),
        "control_profiles": pack.control_profiles,
        "brand": pack.brand,
        "phases": pack.phases,
    }
