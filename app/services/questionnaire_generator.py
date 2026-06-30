"""Generate and update project questionnaires from governance controls."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.models.governance import (
    ControlInstance,
    ControlStatus,
    Project,
    QuestionInstance,
    QuestionnaireInstance,
)
from app.services.control_generator import check_applicability, resolve_control_set
from app.services.schema_service import load_schema

FIELD_CONTROL_MAP: dict[str, list[str]] = {
    "involves_ai_ml": [
        "AI-SEC-01",
        "AI-SEC-02",
        "AI-SEC-03",
        "AI-SEC-05",
        "AI-SEC-06",
        "AI-GOV-01",
    ],
    "ai_eu_risk_class": ["AI-SEC-04", "AI-SEC-07", "AI-GOV-02", "AI-GOV-03"],
    "internet_facing": [
        "GEN-IAM-01",
        "GEN-ENC-01",
        "GEN-VUL-02",
        "GEN-LOG-01",
        "GEN-SEC-02",
    ],
    "data_classification": ["GEN-PRV-01", "GEN-PRV-02", "GEN-ENC-02"],
    "geographic_scope": [
        "CRA-VUL-01",
        "CRA-SBOM-01",
        "EUAI-TR-01",
        "MLPS2-IAM-01",
        "MLPS2-LOG-01",
        "MAS-IAM-01",
        "MAS-LOG-01",
    ],
    "uses_open_source": ["GEN-SC-01", "GEN-SC-02", "GEN-SC-03"],
    "third_party_dependencies": ["GEN-TPR-01", "GEN-SC-01"],
    "hosting_model": ["GEN-ENC-02", "GEN-BCP-01", "GEN-IAM-03"],
    "outsourced_development": ["GEN-TPR-01"],
    "regulatory_obligations": ["GEN-PRV-01", "GEN-PRV-02", "GEN-ENC-02"],
}

GROUP_ORDER = {
    "business_context": 10,
    "system_profile": 20,
    "exposure": 30,
    "data_profile": 40,
    "compliance_scope": 50,
    "ai_profile": 60,
    "supply_chain": 70,
}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _field_control_ids(field: dict[str, Any]) -> list[str]:
    value = field.get("maps_to_controls")
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and value.strip():
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return [
                part.strip().strip("`\"'")
                for part in stripped[1:-1].split(",")
                if part.strip()
            ]
        return [stripped]
    return FIELD_CONTROL_MAP.get(str(field.get("key")), [])


def _is_required(field: dict[str, Any]) -> bool:
    value = field.get("required")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def _questions_for(
    session: Session, questionnaire_id: uuid.UUID
) -> list[QuestionInstance]:
    return session.exec(
        select(QuestionInstance)
        .where(QuestionInstance.questionnaire_id == questionnaire_id)
        .order_by(QuestionInstance.sort_order)
    ).all()


def generate_questionnaire(
    project: Project,
    control_instances: list[ControlInstance],
    session: Session,
) -> tuple[QuestionnaireInstance, list[QuestionInstance]]:
    active_control_ids = {
        control.control_id for control in control_instances if control.is_applicable
    }
    fields = load_schema("phase1_intake").get("fields") or []

    questionnaire = session.exec(
        select(QuestionnaireInstance).where(
            QuestionnaireInstance.project_id == project.id
        )
    ).first()
    if questionnaire is None:
        questionnaire = QuestionnaireInstance(project_id=project.id)
        session.add(questionnaire)
        session.flush()

    questionnaire.generated_from_frameworks = list(project.compliance_frameworks or [])
    existing = {q.question_key: q for q in _questions_for(session, questionnaire.id)}
    order = 0
    for field in fields:
        key = str(field.get("key") or "")
        if not key:
            continue
        mapped_ids = _field_control_ids(field)
        keep = _is_required(field) or bool(active_control_ids.intersection(mapped_ids))
        if not keep:
            continue
        order += 1
        question = existing.get(key)
        if question is None:
            question = QuestionInstance(
                questionnaire_id=questionnaire.id,
                question_key=key,
                question_label=str(field.get("label") or key),
                question_type=str(
                    field.get("field_type") or field.get("question_type") or "text"
                ),
            )
            session.add(question)
        group = str(field.get("group") or "")
        question.question_label = str(field.get("label") or key)
        question.question_type = str(
            field.get("field_type") or field.get("question_type") or "text"
        )
        question.options = _as_list(field.get("options")) or None
        question.group = group or None
        question.ask_when = str(field.get("ask_when") or "") or None
        question.maps_to_control_ids = mapped_ids
        question.sort_order = GROUP_ORDER.get(group, 999) * 100 + order

    session.add(questionnaire)
    session.commit()
    session.refresh(questionnaire)
    return questionnaire, _questions_for(session, questionnaire.id)


def _answers_payload(
    questions: list[QuestionInstance],
    incoming: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for question in questions:
        if question.answer:
            try:
                payload[question.question_key] = json.loads(question.answer)
            except json.JSONDecodeError:
                payload[question.question_key] = question.answer
    payload.update(incoming)
    return payload


def update_applicability_on_answer(
    project_id: uuid.UUID,
    answers: dict[str, Any],
    session: Session,
) -> dict[str, Any]:
    project = session.get(Project, project_id)
    if project is None:
        raise ValueError("Project not found")

    questionnaire = session.exec(
        select(QuestionnaireInstance).where(
            QuestionnaireInstance.project_id == project_id
        )
    ).first()
    if questionnaire is None:
        raise ValueError("Questionnaire not found")

    questions = _questions_for(session, questionnaire.id)
    now = datetime.now(UTC)
    changed_question_controls: set[str] = set()
    for question in questions:
        if question.question_key not in answers:
            continue
        question.answer = json.dumps(answers[question.question_key], ensure_ascii=False)
        question.answered_at = now
        changed_question_controls.update(question.maps_to_control_ids or [])

    all_answers = _answers_payload(questions, answers)
    control_defs = {
        c.control_id: c
        for c in resolve_control_set(project.compliance_frameworks or [])
    }
    controls = session.exec(
        select(ControlInstance).where(ControlInstance.project_id == project_id)
    ).all()

    updated: list[str] = []
    newly_applicable: list[str] = []
    no_longer_applicable: list[str] = []
    for control in controls:
        if (
            changed_question_controls
            and control.control_id not in changed_question_controls
        ):
            continue
        control_def = control_defs.get(control.control_id)
        if control_def is None:
            continue
        before = control.is_applicable
        after, rationale = check_applicability(control_def, all_answers, project)
        if before == after:
            continue
        control.is_applicable = after
        control.applicability_rationale = rationale
        if control.status in {
            ControlStatus.pending.value,
            ControlStatus.not_applicable.value,
        }:
            control.status = (
                ControlStatus.pending.value
                if after
                else ControlStatus.not_applicable.value
            )
        updated.append(control.control_id)
        if after:
            newly_applicable.append(control.control_id)
        else:
            no_longer_applicable.append(control.control_id)

    total_questions = len(questions)
    answered_questions = sum(1 for q in questions if q.answer)
    questionnaire.is_complete = (
        total_questions > 0 and total_questions == answered_questions
    )
    if questionnaire.is_complete and questionnaire.completed_at is None:
        questionnaire.completed_at = now

    session.add(questionnaire)
    session.commit()
    return {
        "answered_count": len(answers),
        "updated_controls": updated,
        "newly_applicable": newly_applicable,
        "no_longer_applicable": no_longer_applicable,
        "questionnaire_complete": questionnaire.is_complete,
    }
