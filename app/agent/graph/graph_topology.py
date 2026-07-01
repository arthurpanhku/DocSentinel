from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from .assessment_graph import compile_assessment_graph
from .state_types import AnalysisState, ConversationState


def _stub_conversation(state: ConversationState) -> ConversationState:
    return state


def _stub_analysis(state: AnalysisState) -> AnalysisState:
    return state


def _route_lifecycle_phase(state: AnalysisState) -> str:
    phase = str(state.get("phase_node") or "phase1").lower()
    return {
        "1": "phase1_intake_classification",
        "phase1": "phase1_intake_classification",
        "phase2": "phase2_threat_modeling_requirements",
        "2": "phase2_threat_modeling_requirements",
        "phase3": "phase3_secure_design_review",
        "3": "phase3_secure_design_review",
        "phase4": "phase4_secure_build_supply_chain",
        "4": "phase4_secure_build_supply_chain",
        "phase5": "phase5_control_verification",
        "5": "phase5_control_verification",
        "phase6": "phase6_release_certification",
        "6": "phase6_release_certification",
    }.get(phase, "phase1_intake_classification")


def compile_ssdlc_lifecycle_parent_topology() -> Any:
    graph = StateGraph(AnalysisState)
    graph.add_node("classify_active_phase", _stub_analysis)
    graph.add_node("phase1_intake_classification", _stub_analysis)
    graph.add_node("phase2_threat_modeling_requirements", _stub_analysis)
    graph.add_node("phase3_secure_design_review", _stub_analysis)
    graph.add_node("phase4_secure_build_supply_chain", _stub_analysis)
    graph.add_node("phase5_control_verification", _stub_analysis)
    graph.add_node("phase6_release_certification", _stub_analysis)
    graph.add_node("persist_phase_state", _stub_analysis)
    graph.add_edge(START, "classify_active_phase")
    graph.add_conditional_edges(
        "classify_active_phase",
        _route_lifecycle_phase,
        {
            "phase1_intake_classification": "phase1_intake_classification",
            "phase2_threat_modeling_requirements": (
                "phase2_threat_modeling_requirements"
            ),
            "phase3_secure_design_review": "phase3_secure_design_review",
            "phase4_secure_build_supply_chain": "phase4_secure_build_supply_chain",
            "phase5_control_verification": "phase5_control_verification",
            "phase6_release_certification": "phase6_release_certification",
        },
    )
    for node in (
        "phase1_intake_classification",
        "phase2_threat_modeling_requirements",
        "phase3_secure_design_review",
        "phase4_secure_build_supply_chain",
        "phase5_control_verification",
        "phase6_release_certification",
    ):
        graph.add_edge(node, "persist_phase_state")
    graph.add_edge("persist_phase_state", END)
    return graph.compile()


def compile_phase1_intake_classification_topology() -> Any:
    graph = StateGraph(ConversationState)
    graph.add_node("collect_project_context", _stub_conversation)
    graph.add_node("classify_security_scope", _stub_conversation)
    graph.add_node("select_framework_profile", _stub_conversation)
    graph.add_node("generate_intake_summary", _stub_conversation)
    graph.add_edge(START, "collect_project_context")
    graph.add_edge("collect_project_context", "classify_security_scope")
    graph.add_edge("classify_security_scope", "select_framework_profile")
    graph.add_edge("select_framework_profile", "generate_intake_summary")
    graph.add_edge("generate_intake_summary", END)
    return graph.compile()


def compile_phase3_secure_design_review_topology() -> Any:
    graph = StateGraph(AnalysisState)
    graph.add_node("review_secure_design", _stub_analysis)
    graph.add_node("validate_identity_design", _stub_analysis)
    graph.add_node("validate_data_protection_design", _stub_analysis)
    graph.add_node("record_design_findings", _stub_analysis)
    graph.add_edge(START, "review_secure_design")
    graph.add_edge("review_secure_design", "validate_identity_design")
    graph.add_edge("validate_identity_design", "validate_data_protection_design")
    graph.add_edge("validate_data_protection_design", "record_design_findings")
    graph.add_edge("record_design_findings", END)
    return graph.compile()


def mermaid_ssdlc_lifecycle() -> str:
    return compile_ssdlc_lifecycle_parent_topology().get_graph(xray=True).draw_mermaid()


GRAPH_REGISTRY: dict[str, tuple[str, Any]] = {
    "docsentinel_assessment": (
        "DocSentinel assessment workflow",
        compile_assessment_graph,
    ),
    "ssdlc_lifecycle_parent": (
        "SSDLC lifecycle parent workflow",
        compile_ssdlc_lifecycle_parent_topology,
    ),
    "phase1_intake_classification": (
        "Phase 1: Intake & Classification",
        compile_phase1_intake_classification_topology,
    ),
    "phase3_secure_design_review": (
        "Phase 3: Secure Design Review",
        compile_phase3_secure_design_review_topology,
    ),
}
