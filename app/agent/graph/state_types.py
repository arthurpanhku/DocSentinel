from __future__ import annotations

from typing import Annotated, Any, NotRequired, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.models.assessment import AssessmentReport
from app.models.parser import ParsedDocument


class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_phase: str
    form_data: dict[str, Any]
    completed_fields: list[str]
    session_id: str
    current_field: str | None
    intent: str | None
    client_subagent_lane: NotRequired[str | None]
    kb_context: list[dict]
    validation_error: str | None
    gate_complete: bool
    retry_count: int
    compliance_frameworks: NotRequired[list[str]]
    ai_system: NotRequired[bool]
    response_language: NotRequired[str]


class AnalysisState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    requirement_id: str
    requirement: dict
    evidences: list[dict]
    vision_results: list[dict]
    kb_context: list[dict]
    analysis_result: dict | None
    recommendation: str | None
    error: str | None
    phase_node: NotRequired[str | None]
    control_frameworks: NotRequired[list[str]]


class AssessmentGraphState(TypedDict, total=False):
    task_id: UUID
    parsed_documents: list[ParsedDocument]
    scenario_id: str | None
    project_id: str | None
    phase: str | None
    skill_id: str | None
    skill: Any
    doc_context: dict[str, str]
    policy_chunks: list[Any]
    history_chunks: list[Any]
    evidence_context: str
    draft_raw: str
    reviewed_raw: str
    report: AssessmentReport
    persisted_controls: int
