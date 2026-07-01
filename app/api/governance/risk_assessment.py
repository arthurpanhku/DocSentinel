from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.s2o_rule_engine import get_engine

from .utils import ok

router = APIRouter(tags=["governance-risk-assessment"])


class S2OEvaluationRequest(BaseModel):
    data_classification: str
    access: str
    solution_type: str
    hosting_environment: str
    release_type: str


@router.post("/risk-assessment/evaluate")
async def evaluate_risk_assessment(
    request: S2OEvaluationRequest,
) -> dict[str, Any]:
    result = get_engine().evaluate(
        data_classification=request.data_classification,
        access=request.access,
        solution_type=request.solution_type,
        hosting_environment=request.hosting_environment,
        release_type=request.release_type,
    )
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["invalid_reason"],
        )
    return ok(result)


@router.post("/risk-assessment/reload")
async def reload_risk_ontology() -> dict[str, Any]:
    get_engine().reload()
    return ok({"message": "Risk assessment ontology reloaded from YAML."})


@router.post("/s2o/evaluate")
async def evaluate_legacy_s2o(request: S2OEvaluationRequest) -> dict[str, Any]:
    return await evaluate_risk_assessment(request)
