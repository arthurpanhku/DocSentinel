from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

from . import (
    admin,
    auth,
    controls,
    exports,
    projects,
    questionnaire,
    risk_assessment,
    schemas,
    sub_agents,
    submissions,
)

router = APIRouter()
router.include_router(auth.router)
protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(schemas.router)
protected.include_router(exports.router)
protected.include_router(projects.router)
protected.include_router(controls.router)
protected.include_router(questionnaire.router)
protected.include_router(submissions.router)
protected.include_router(risk_assessment.router)
protected.include_router(sub_agents.router)
protected.include_router(admin.router)
router.include_router(protected)
