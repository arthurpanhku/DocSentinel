from __future__ import annotations

# ruff: noqa: B008
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.deps import get_current_user
from app.models.governance import ControlInstance, QuestionnaireInstance
from app.services.questionnaire_generator import (
    generate_questionnaire,
    update_applicability_on_answer,
)

from .utils import get_project_or_404, ok, serialize_questionnaire, write_audit_event

router = APIRouter(
    prefix="/projects/{project_id}/questionnaire",
    tags=["governance-questionnaire"],
)


class SubmitAnswersRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def get_questionnaire(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    project = get_project_or_404(project_id, session, current_user)
    questionnaire = session.exec(
        select(QuestionnaireInstance).where(
            QuestionnaireInstance.project_id == project_id
        )
    ).first()
    if questionnaire is None:
        controls = session.exec(
            select(ControlInstance).where(ControlInstance.project_id == project_id)
        ).all()
        if not controls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generate controls first",
            )
        questionnaire, questions = generate_questionnaire(project, controls, session)
    else:
        from app.services.questionnaire_generator import _questions_for

        questions = _questions_for(session, questionnaire.id)
    return ok(serialize_questionnaire(questionnaire, questions))


@router.post("/answers")
async def submit_answers(
    project_id: uuid.UUID,
    payload: SubmitAnswersRequest,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    try:
        result = update_applicability_on_answer(project_id, payload.answers, session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    write_audit_event(
        session,
        actor=current_user,
        action="questionnaire.answers.submit",
        resource_type="project",
        resource_id=str(project_id),
        details={"answer_count": len(payload.answers)},
    )
    session.commit()
    return ok(result)


@router.get("/progress")
async def get_questionnaire_progress(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    get_project_or_404(project_id, session, current_user)
    questionnaire = session.exec(
        select(QuestionnaireInstance).where(
            QuestionnaireInstance.project_id == project_id
        )
    ).first()
    if questionnaire is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found",
        )
    from app.services.questionnaire_generator import _questions_for

    questions = _questions_for(session, questionnaire.id)
    total = len(questions)
    answered = sum(1 for question in questions if question.answer)
    percent = round((answered / total) * 100, 1) if total else 0
    return ok(
        {
            "total": total,
            "answered": answered,
            "required_total": total,
            "required_answered": answered,
            "percent": percent,
        }
    )
