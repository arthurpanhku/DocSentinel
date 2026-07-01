from __future__ import annotations

# ruff: noqa: B008
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.db import get_session
from app.services.oscal_export import (
    build_oscal_catalog,
    build_project_assessment_results,
)

from .utils import get_project_or_404, ok

router = APIRouter(tags=["governance-exports"])


@router.get("/oscal/catalog")
async def export_oscal_catalog(
    framework_ids: list[str] = Query(default=[]),
) -> dict[str, Any]:
    """Export resolved policy-pack controls in an OSCAL catalog-like shape."""

    return ok(
        build_oscal_catalog(framework_ids),
        {
            "format": "oscal-catalog",
            "framework_ids": framework_ids,
        },
    )


@router.get("/projects/{project_id}/oscal/assessment-results")
async def export_project_oscal_assessment_results(
    project_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Export project controls, evidence, and findings as OSCAL assessment results."""

    project = get_project_or_404(project_id, session)
    return ok(
        build_project_assessment_results(project, session),
        {
            "format": "oscal-assessment-results",
            "project_id": str(project_id),
        },
    )
