"""Deterministic risk and control applicability rule engine.

The public API name is ``risk-assessment``. Historical imports still use this
module name for compatibility, but the implementation is vendor-neutral and
does not depend on offline workbook or HTML tools.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ONTOLOGY_PATH = (
    Path(__file__).resolve().parents[2]
    / "policy_packs"
    / "generic-ssdlc"
    / "risk_ontology.yaml"
)

_DEFAULT_ONTOLOGY: dict[str, Any] = {
    "hosting_environment_by_solution_type": {
        "1": {"1": "Cloud", "2": "On-premises", "3": "Hybrid", "4": "Managed platform"},
        "2": {"40": "Third-party SaaS", "41": "Third-party managed service"},
        "3": {"50": "Desktop or endpoint"},
        "4": {"60": "Script or automation"},
        "5": {"70": "RPA or workflow automation"},
        "6": {"80": "Other"},
    },
    "risk_logic": {
        "implemented_risk_rating_rules": [
            {
                "rule_id": "RR-001",
                "when": {"data_classification_in": ["1", "2"], "access": "1"},
                "then": {"risk_rating": "high"},
            },
            {
                "rule_id": "RR-002",
                "when": {"data_classification": "1"},
                "then": {"risk_rating": "high"},
            },
            {
                "rule_id": "RR-003",
                "when": {"data_classification": "2"},
                "then": {"risk_rating": "medium"},
            },
            {
                "rule_id": "RR-004",
                "when": {"data_classification": "3"},
                "then": {"risk_rating": "low"},
            },
        ],
        "risk_level_rules": [
            {
                "rule_id": "RL-001",
                "when": {"data_classification": "1", "access": "1"},
                "then": {"risk_level": "1"},
            },
            {
                "rule_id": "RL-002",
                "when": {"data_classification": "1", "access": "2"},
                "then": {"risk_level": "2"},
            },
            {
                "rule_id": "RL-003",
                "when": {"data_classification": "2", "access": "1"},
                "then": {"risk_level": "3"},
            },
            {
                "rule_id": "RL-004",
                "when": {"data_classification": "2", "access": "2"},
                "then": {"risk_level": "4"},
            },
            {
                "rule_id": "RL-005",
                "when": {"data_classification": "3", "access": "1"},
                "then": {"risk_level": "5"},
            },
            {
                "rule_id": "RL-006",
                "when": {"data_classification": "3", "access": "2"},
                "then": {"risk_level": "6"},
            },
        ],
        "known_logic_gaps": [],
    },
    "requirement_tokens": {
        "REQ_SECURITY_INTAKE": "Security intake and classification",
        "REQ_THREAT_MODEL": "Threat modeling and security requirements",
        "REQ_DESIGN_REVIEW": "Secure design review",
        "REQ_BUILD_SECURITY": "Secure build and supply-chain evidence",
        "REQ_CONTROL_VERIFICATION": "Security control verification",
        "REQ_RELEASE_CERTIFICATION": "Release review and SSDLC certificate readiness",
    },
    "requirements_logic": {
        "release_type_1_new_or_major": [
            {
                "rule_id": "NR-001",
                "when": {},
                "then": {
                    "requirements": [
                        "REQ_SECURITY_INTAKE",
                        "REQ_THREAT_MODEL",
                        "REQ_DESIGN_REVIEW",
                        "REQ_BUILD_SECURITY",
                        "REQ_CONTROL_VERIFICATION",
                        "REQ_RELEASE_CERTIFICATION",
                    ]
                },
            }
        ],
        "release_type_2_minor": [
            {
                "rule_id": "MR-001",
                "when": {},
                "then": {
                    "requirements": [
                        "REQ_SECURITY_INTAKE",
                        "REQ_BUILD_SECURITY",
                        "REQ_CONTROL_VERIFICATION",
                        "REQ_RELEASE_CERTIFICATION",
                    ],
                    "conditional_additions": [
                        {
                            "when": {"risk_rating_in": ["high", "medium"]},
                            "add": ["REQ_THREAT_MODEL", "REQ_DESIGN_REVIEW"],
                        }
                    ],
                },
            }
        ],
    },
    "post_rules": [],
    "full_ssdlc_control_applicability": {"exclusion_rules": []},
}

INVALID_TOKEN = "invalid_selection"
FULL_SSDLC_PROFILE = "full_ssdlc"
ESSENTIAL_SSDLC_PROFILE = "essential_ssdlc"

# ---------------------------------------------------------------------------
# Data classes (plain dicts kept intentional – no Pydantic dependency here)
# ---------------------------------------------------------------------------


def _load_ontology(path: Path = _ONTOLOGY_PATH) -> dict[str, Any]:
    if not path.exists():
        return _DEFAULT_ONTOLOGY
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def _cached_ontology() -> dict[str, Any]:
    return _load_ontology()


def reload_ontology() -> None:
    """Force reload of the risk ontology (clears lru_cache)."""
    _cached_ontology.cache_clear()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_hosting_env(
    solution_type: str, hosting_environment: str, ontology: dict
) -> bool:
    mapping: dict = ontology.get("hosting_environment_by_solution_type", {})
    allowed = mapping.get(solution_type, {})
    return hosting_environment in allowed


# ---------------------------------------------------------------------------
# Risk rating evaluation
# ---------------------------------------------------------------------------


def _evaluate_risk(
    data_classification: str,
    access: str,
    ontology: dict,
) -> tuple[str, str, list[str]]:
    """
    Returns (risk_rating, risk_level, matched_rule_ids).

    risk_rating: "high" | "medium" | "low" | "unknown"
    risk_level: "1"–"6" | "unknown"
    """
    risk_logic: dict = ontology.get("risk_logic", {})

    # --- risk_rating (first-match-wins, mirrors JS execution order) ---
    risk_rating = "unknown"
    rr_rules: list[dict] = risk_logic.get("implemented_risk_rating_rules", [])
    matched_rr: list[str] = []

    for rule in rr_rules:
        when = rule.get("when", {})
        rule_id: str = rule["rule_id"]

        dc_in = when.get("data_classification_in")
        dc_eq = when.get("data_classification")
        acc_eq = when.get("access")

        dc_match = (dc_in and data_classification in dc_in) or (
            dc_eq and data_classification == dc_eq
        )
        acc_match = acc_eq is None or access == acc_eq

        if dc_match and acc_match:
            risk_rating = rule["then"]["risk_rating"]
            matched_rr.append(rule_id)
            break  # first-match-wins

    # --- risk_level (independent, exhaustive lookup) ---
    risk_level = "unknown"
    rl_rules: list[dict] = risk_logic.get("risk_level_rules", [])
    matched_rl: list[str] = []

    for rule in rl_rules:
        when = rule.get("when", {})
        rule_id = rule["rule_id"]
        if (
            when.get("data_classification") == data_classification
            and when.get("access") == access
        ):
            risk_level = rule["then"]["risk_level"]
            matched_rl.append(rule_id)
            break

    return risk_rating, risk_level, matched_rr + matched_rl


# ---------------------------------------------------------------------------
# Requirement rule evaluation
# ---------------------------------------------------------------------------


def _eval_condition(
    when: dict,
    risk_rating: str,
    risk_level: str,
    access: str,
    solution_type: str,
    hosting_environment: str,
    data_classification: str,
) -> bool:
    """Check whether a single rule's `when` clause matches the inputs."""
    # solution_type checks
    st = when.get("solution_type")
    st_in = when.get("solution_type_in")
    st_not = when.get("solution_type_not")
    if st and solution_type != st:
        return False
    if st_in and solution_type not in st_in:
        return False
    if st_not and solution_type == st_not:
        return False

    # risk_rating checks
    rr = when.get("risk_rating")
    rr_in = when.get("risk_rating_in")
    if rr and risk_rating != rr:
        return False
    if rr_in and risk_rating not in rr_in:
        return False

    # hosting_environment checks
    he = when.get("hosting_environment")
    he_in = when.get("hosting_environment_in")
    if he and hosting_environment != he:
        return False
    if he_in and hosting_environment not in he_in:
        return False

    # access checks
    acc = when.get("access")
    if acc and access != acc:
        return False

    # data_classification checks
    dc = when.get("data_classification")
    if dc and data_classification != dc:
        return False

    # risk_level checks
    rl_in = when.get("risk_level_in")
    if rl_in and risk_level not in rl_in:
        return False

    return True


def _evaluate_requirements(
    risk_rating: str,
    risk_level: str,
    access: str,
    solution_type: str,
    hosting_environment: str,
    data_classification: str,
    release_type: str,
    ontology: dict,
) -> tuple[list[str], list[str]]:
    """
    Returns (requirement_tokens, matched_rule_ids).

    Applies:
    1. Base rules (NR-xxx for new/major, MR-xxx for minor)
    2. Conditional additions within matched base rule
    3. Post-rules (POST-001, POST-002)
    """
    req_logic: dict = ontology.get("requirements_logic", {})
    tokens: dict[str, str] = ontology.get("requirement_tokens", {})
    matched_rules: list[str] = []
    requirements: list[str] = []

    # Select rule group by release_type
    if release_type == "1":
        base_rules: list[dict] = req_logic.get("release_type_1_new_or_major", [])
    else:
        base_rules = req_logic.get("release_type_2_minor", [])

    # Find first matching base rule
    for rule in base_rules:
        rule_id: str = rule["rule_id"]
        when = rule.get("when", {})

        if _eval_condition(
            when,
            risk_rating,
            risk_level,
            access,
            solution_type,
            hosting_environment,
            data_classification,
        ):
            matched_rules.append(rule_id)
            then = rule.get("then", {})

            # Base requirements
            for token_key in then.get("requirements", []):
                label = tokens.get(token_key, token_key)
                if label not in requirements:
                    requirements.append(label)

            # Conditional additions
            for cond in then.get("conditional_additions", []):
                cond_when = cond.get("when", {})
                if _eval_condition(
                    cond_when,
                    risk_rating,
                    risk_level,
                    access,
                    solution_type,
                    hosting_environment,
                    data_classification,
                ):
                    for token_key in cond.get("add", []):
                        label = tokens.get(token_key, token_key)
                        if label not in requirements:
                            requirements.append(label)
            break  # first-match-wins for base rules

    # Post-rules (always evaluated after base rules)
    post_rules: list[dict] = ontology.get("post_rules", [])
    for rule in post_rules:
        rule_id = rule["rule_id"]
        when = rule.get("when", {})

        if _eval_condition(
            when,
            risk_rating,
            risk_level,
            access,
            solution_type,
            hosting_environment,
            data_classification,
        ):
            matched_rules.append(rule_id)
            for token_key in rule.get("then", {}).get("append_requirements", []):
                label = tokens.get(token_key, token_key)
                if label not in requirements:
                    requirements.append(label)

    return requirements, matched_rules


# ---------------------------------------------------------------------------
# Known gap detection
# ---------------------------------------------------------------------------


def _eval_control_exclusion_rule(
    rule: dict, control_family: str, project_attrs: dict[str, Any]
) -> bool:
    """Return True if the control should be excluded (rule fires = not applicable)."""
    when = rule.get("when", {})

    # Check control family prefix — must match for rule to apply
    prefix = when.get("control_family_prefix")
    if prefix and not control_family.startswith(prefix):
        return False

    # Check boolean project attributes
    for bool_key in (
        "is_iot",
        "is_ai",
        "is_rpa",
        "is_power_platform",
        "is_vertex_ai",
        "is_china_mf",
    ):
        if bool_key in when:
            expected = when[bool_key]
            actual = bool(project_attrs.get(bool_key, False))
            if actual != expected:
                return False

    # Check string project attributes
    if "access" in when:
        if str(project_attrs.get("access", "")) != str(when["access"]):
            return False
    if "solution_type" in when:
        if str(project_attrs.get("solution_type", "")) != str(when["solution_type"]):
            return False

    return True


def _detect_known_gaps(
    data_classification: str, access: str, ontology: dict
) -> list[str]:
    gaps: list[dict] = ontology.get("risk_logic", {}).get("known_logic_gaps", [])
    triggered: list[str] = []
    # GAP-001: (dc=2, access=1) resolves as High; Medium branch unreachable
    for gap in gaps:
        if gap["gap_id"] == "GAP-001" and data_classification == "2" and access == "1":
            triggered.append(gap["gap_id"])
    return triggered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class S2ORuleEngine:
    """Evaluate deterministic risk and control applicability rules.

    Usage:
        engine = S2ORuleEngine()
        result = engine.evaluate(
            data_classification="1",
            access="1",
            solution_type="1",
            hosting_environment="2",
            release_type="1",
        )
    """

    def __init__(self, ontology: dict[str, Any] | None = None) -> None:
        self._ontology = ontology  # None = use cached global

    def _get_ontology(self) -> dict[str, Any]:
        return self._ontology if self._ontology is not None else _cached_ontology()

    def evaluate(
        self,
        data_classification: str,
        access: str,
        solution_type: str,
        hosting_environment: str,
        release_type: str,
    ) -> dict[str, Any]:
        """
        Evaluate the full risk and control-profile decision matrix.

        Returns:
            {
                "risk_rating": str,
                "risk_level": str,
                "control_profile": str,
                "requirements": list[str],
                "matched_rules": list[str],
                "known_gaps": list[str],
                "valid": bool,
                "invalid_reason": str | None,
            }
        """
        ontology = self._get_ontology()

        # Validate hosting_environment against solution_type
        if not _validate_hosting_env(solution_type, hosting_environment, ontology):
            return {
                "risk_rating": "unknown",
                "risk_level": "unknown",
                "requirements": [INVALID_TOKEN],
                "matched_rules": [],
                "known_gaps": [],
                "valid": False,
                "invalid_reason": (
                    f"hosting_environment '{hosting_environment}' is not valid "
                    f"for solution_type '{solution_type}'"
                ),
            }

        # Step 1: Risk rating + level
        risk_rating, risk_level, risk_rules = _evaluate_risk(
            data_classification, access, ontology
        )
        # risk_level 1-3 -> Full SSDLC; 4-6 (or unknown) -> Essential SSDLC.
        control_profile = (
            FULL_SSDLC_PROFILE
            if str(risk_level) in {"1", "2", "3"}
            else ESSENTIAL_SSDLC_PROFILE
        )

        # Step 2: Requirements
        requirements, req_rules = _evaluate_requirements(
            risk_rating,
            risk_level,
            access,
            solution_type,
            hosting_environment,
            data_classification,
            release_type,
            ontology,
        )

        # Step 3: Known gaps
        known_gaps = _detect_known_gaps(data_classification, access, ontology)

        return {
            "risk_rating": risk_rating,
            "risk_level": risk_level,
            "control_profile": control_profile,
            "requirements": requirements,
            "matched_rules": risk_rules + req_rules,
            "known_gaps": known_gaps,
            "valid": True,
            "invalid_reason": None,
        }

    def evaluate_applicable_controls(
        self,
        control_catalog: list[dict[str, Any]],
        project_attrs: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Filter a Full SSDLC control catalog by applicability rules.

        project_attrs keys (all optional, default False/empty):
          is_iot, is_ai, is_rpa, is_power_platform, is_vertex_ai, is_china_mf (bool)
          access, solution_type (str, same codes as risk ontology dimensions)

        Returns each control annotated with:
          applicable (bool), matched_rules (list[str]), applicability_reason (str)
        """
        ontology = self._get_ontology()
        exclusion_rules: list[dict] = ontology.get(
            "full_ssdlc_control_applicability", {}
        ).get("exclusion_rules", [])

        result: list[dict[str, Any]] = []
        for ctrl in control_catalog:
            control_id = ctrl.get("control_id", "")
            family = ctrl.get("family", "").strip("`").strip()
            # Fall back to extracting family from control_id prefix.
            if not family and "-" in control_id:
                family = "-".join(control_id.split("-")[:-1])

            matched: list[str] = []
            reason = ""
            applicable = True

            for rule in exclusion_rules:
                if _eval_control_exclusion_rule(rule, family, project_attrs):
                    applicable = False
                    matched.append(rule["rule_id"])
                    reason = rule.get("then", {}).get(
                        "reason", "Excluded by ontology rule"
                    )
                    break  # first-match wins

            if applicable:
                reason = "Default applicable — no exclusion rule matched"

            annotated = dict(ctrl)
            annotated["applicable"] = applicable
            annotated["matched_rules"] = matched
            annotated["applicability_reason"] = reason
            result.append(annotated)

        return result

    def reload(self) -> None:
        """Reload the risk ontology (only applies to the global cached version)."""
        reload_ontology()


# Module-level singleton for use in route handlers
_engine: S2ORuleEngine | None = None


def get_engine() -> S2ORuleEngine:
    global _engine
    if _engine is None:
        _engine = S2ORuleEngine()
    return _engine
