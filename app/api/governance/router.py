from fastapi import APIRouter

from . import (
    admin,
    auth,
    controls,
    projects,
    questionnaire,
    risk_assessment,
    schemas,
    sub_agents,
    submissions,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(schemas.router)
router.include_router(projects.router)
router.include_router(controls.router)
router.include_router(questionnaire.router)
router.include_router(submissions.router)
router.include_router(risk_assessment.router)
router.include_router(sub_agents.router)
router.include_router(admin.router)
