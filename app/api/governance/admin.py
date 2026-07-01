from __future__ import annotations

# ruff: noqa: B008
import json
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.governance import (
    GovernanceAuditLog,
    KnowledgeBaseType,
    Language,
    OrgFrameworkConfig,
    PolicyDocument,
    Project,
    PromptAuditLog,
)
from app.services.control_generator import (
    generate_controls_for_project,
    resolve_control_set,
)
from app.services.graphify_kb import GRAPH_DIR, RAW_DIR, parse_document, write_artifacts
from app.services.policy_pack import list_overlay_packs

from .utils import iso, ok

router = APIRouter(tags=["governance-admin"])


class OrgFrameworkConfigUpdate(BaseModel):
    framework_ids: list[str] = Field(default_factory=list)
    default_review_mode: Literal["ai_first", "human_only", "ai_only"] = "ai_first"
    require_human_for_high_risk_ai: bool = True
    updated_by_id: int | None = None


class GenerateControlsRequest(BaseModel):
    framework_ids: list[str] = Field(default_factory=list)


def _serialize_org_config(config: OrgFrameworkConfig) -> dict[str, Any]:
    return {
        "id": str(config.id),
        "framework_ids": config.framework_ids or [],
        "default_review_mode": config.default_review_mode,
        "require_human_for_high_risk_ai": config.require_human_for_high_risk_ai,
        "created_by_id": config.created_by_id,
        "updated_by_id": config.updated_by_id,
        "created_at": iso(config.created_at),
        "updated_at": iso(config.updated_at),
    }


def _get_or_create_org_config(session: Session) -> OrgFrameworkConfig:
    config = session.exec(
        select(OrgFrameworkConfig).order_by(OrgFrameworkConfig.updated_at.desc())
    ).first()
    if config is not None:
        return config
    config = OrgFrameworkConfig(
        framework_ids=[],
        default_review_mode="ai_first",
        require_human_for_high_risk_ai=True,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@router.get("/admin/frameworks")
async def list_admin_frameworks() -> dict[str, Any]:
    frameworks = list_overlay_packs()
    return ok(frameworks, {"count": len(frameworks)})


@router.get("/admin/org-config/frameworks")
async def get_org_framework_config(
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return ok(_serialize_org_config(_get_or_create_org_config(session)))


@router.put("/admin/org-config/frameworks")
async def update_org_framework_config(
    payload: OrgFrameworkConfigUpdate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if not payload.framework_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one compliance framework must be selected.",
        )
    config = _get_or_create_org_config(session)
    config.framework_ids = payload.framework_ids
    config.default_review_mode = payload.default_review_mode
    config.require_human_for_high_risk_ai = payload.require_human_for_high_risk_ai
    config.updated_by_id = payload.updated_by_id
    session.add(config)
    session.commit()
    session.refresh(config)

    projects = session.exec(
        select(Project).where(Project.framework_ids_locked.is_(False))
    ).all()
    generated = []
    for project in projects:
        summary = generate_controls_for_project(
            project=project,
            intake_payload={},
            framework_ids=list(project.compliance_frameworks or payload.framework_ids),
            review_mode=project.review_mode or payload.default_review_mode,
            session=session,
            regenerate=False,
        )
        generated.append({"project_id": str(project.id), **summary})
    return ok(
        _serialize_org_config(config),
        {"auto_build": {"count": len(generated), "projects": generated}},
    )


@router.post("/admin/org-config/preview-controls")
async def preview_controls_for_frameworks(
    payload: GenerateControlsRequest,
) -> dict[str, Any]:
    controls = resolve_control_set(payload.framework_ids)
    by_framework: dict[str, int] = {}
    data: list[dict[str, Any]] = []
    for control in controls:
        for framework_id in control.source_frameworks:
            by_framework[framework_id] = by_framework.get(framework_id, 0) + 1
        data.append(
            {
                "control_id": control.control_id,
                "family": control.family,
                "title": control.title,
                "source_frameworks": control.source_frameworks,
                "expected_evidence": control.expected_evidence,
            }
        )
    return ok({"controls": data, "by_framework": by_framework, "total": len(data)})


@router.post("/knowledge/upload", status_code=status.HTTP_201_CREATED)
async def upload_policy_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    language: str = Form("en"),
    doc_type: str = Form("policy"),
    version: str = Form("1.0"),
    kb_type: str = Form("user_side"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    try:
        lang = Language(language)
        kb = KnowledgeBaseType(kb_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    suffix = Path(file.filename or "upload").suffix.lower() or ".txt"
    if suffix not in {".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv", ".json"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{suffix}'",
        )
    doc_id = uuid.uuid4()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    local_path = RAW_DIR / f"{doc_id}{suffix}"
    local_path.write_bytes(await file.read())
    try:
        parsed = parse_document(local_path, suffix)
        artifacts = write_artifacts(
            doc_id=doc_id,
            title=title,
            filename=file.filename or local_path.name,
            parsed=parsed,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document parsing failed: {exc}",
        ) from exc
    doc = PolicyDocument(
        id=doc_id,
        title=title,
        language=lang.value,
        doc_type=doc_type,
        file_path=str(local_path),
        version=version,
        is_active=True,
        kb_type=kb.value,
    )
    session.add(doc)
    session.commit()
    return ok(
        {
            "id": str(doc.id),
            "title": doc.title,
            "language": doc.language,
            "kb_type": doc.kb_type,
            "version": doc.version,
            "file_path": doc.file_path,
            "graphify": artifacts,
        }
    )


@router.get("/knowledge/documents")
async def list_policy_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    docs = session.exec(
        select(PolicyDocument)
        .order_by(PolicyDocument.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return ok(
        [
            {
                "id": str(doc.id),
                "title": doc.title,
                "language": doc.language,
                "doc_type": doc.doc_type,
                "version": doc.version,
                "kb_type": doc.kb_type,
                "file_path": doc.file_path,
                "is_active": doc.is_active,
                "created_at": iso(doc.created_at),
            }
            for doc in docs
        ],
        {"skip": skip, "limit": limit, "count": len(docs)},
    )


@router.get("/knowledge/documents/{doc_id}/graph")
async def get_policy_document_graph(doc_id: uuid.UUID) -> dict[str, Any]:
    graph_path = GRAPH_DIR / f"{doc_id}.json"
    if not graph_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph artifact not found",
        )
    return ok(json.loads(graph_path.read_text(encoding="utf-8")))


@router.get("/audit-log")
async def get_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    logs = session.exec(
        select(GovernanceAuditLog)
        .order_by(GovernanceAuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return ok(
        [
            {
                "id": str(row.id),
                "user_id": row.user_id,
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "details": row.details or {},
                "created_at": iso(row.created_at),
            }
            for row in logs
        ],
        {"skip": skip, "limit": limit, "count": len(logs)},
    )


@router.get("/prompt-audit-log")
async def get_prompt_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    rows = session.exec(
        select(PromptAuditLog)
        .order_by(PromptAuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return ok(
        [
            {
                "id": str(row.id),
                "user_id": row.user_id,
                "project_id": str(row.project_id) if row.project_id else None,
                "mvp_task": row.mvp_task,
                "model": row.model,
                "prompt_digest": row.prompt_digest,
                "response_digest": row.response_digest,
                "token_count_in": row.token_count_in,
                "token_count_out": row.token_count_out,
                "pii_fields_redacted": row.pii_fields_redacted or [],
                "safety": row.safety or {},
                "created_at": iso(row.created_at),
            }
            for row in rows
        ],
        {"skip": skip, "limit": limit, "count": len(rows)},
    )
