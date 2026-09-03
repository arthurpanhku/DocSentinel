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
from app.core.deps import get_current_user
from app.core.security import ensure_role
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

from .utils import iso, ok, write_audit_event

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
        "tenant_id": config.tenant_id,
        "framework_ids": config.framework_ids or [],
        "default_review_mode": config.default_review_mode,
        "require_human_for_high_risk_ai": config.require_human_for_high_risk_ai,
        "created_by_id": config.created_by_id,
        "updated_by_id": config.updated_by_id,
        "created_at": iso(config.created_at),
        "updated_at": iso(config.updated_at),
    }


def _get_or_create_org_config(
    session: Session,
    current_user: Any,
) -> OrgFrameworkConfig:
    config = session.exec(
        select(OrgFrameworkConfig)
        .where(OrgFrameworkConfig.tenant_id == current_user.tenant_id)
        .order_by(OrgFrameworkConfig.updated_at.desc())
    ).first()
    if config is not None:
        return config
    config = OrgFrameworkConfig(
        framework_ids=[],
        default_review_mode="ai_first",
        require_human_for_high_risk_ai=True,
        tenant_id=current_user.tenant_id,
        created_by_id=current_user.id,
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
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    return ok(_serialize_org_config(_get_or_create_org_config(session, current_user)))


@router.put("/admin/org-config/frameworks")
async def update_org_framework_config(
    payload: OrgFrameworkConfigUpdate,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_role(current_user, "admin")
    if not payload.framework_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one compliance framework must be selected.",
        )
    config = _get_or_create_org_config(session, current_user)
    config.framework_ids = payload.framework_ids
    config.default_review_mode = payload.default_review_mode
    config.require_human_for_high_risk_ai = payload.require_human_for_high_risk_ai
    config.updated_by_id = current_user.id
    session.add(config)
    write_audit_event(
        session,
        actor=current_user,
        action="organization.frameworks.update",
        resource_type="organization_config",
        resource_id=str(config.id),
        details={"framework_ids": payload.framework_ids},
    )
    session.commit()
    session.refresh(config)

    projects = session.exec(
        select(Project).where(
            Project.tenant_id == current_user.tenant_id,
            Project.framework_ids_locked.is_(False),
        )
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
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_role(current_user, "admin", "security_reviewer", "auditor")
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
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_role(current_user, "admin")
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
        tenant_id=current_user.tenant_id,
        title=title,
        language=lang.value,
        doc_type=doc_type,
        file_path=str(local_path),
        version=version,
        is_active=True,
        kb_type=kb.value,
        uploaded_by_id=current_user.id,
    )
    session.add(doc)
    write_audit_event(
        session,
        actor=current_user,
        action="knowledge.document.upload",
        resource_type="policy_document",
        resource_id=str(doc.id),
        details={"title": title, "version": version},
    )
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
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    docs = session.exec(
        select(PolicyDocument)
        .where(PolicyDocument.tenant_id == current_user.tenant_id)
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
async def get_policy_document_graph(
    doc_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    document = session.get(PolicyDocument, doc_id)
    if document is None or document.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy document not found",
        )
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
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    logs = session.exec(
        select(GovernanceAuditLog)
        .where(GovernanceAuditLog.tenant_id == current_user.tenant_id)
        .order_by(GovernanceAuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return ok(
        [
            {
                "id": str(row.id),
                "user_id": row.user_id,
                "tenant_id": row.tenant_id,
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "details": row.details or {},
                "outcome": row.outcome,
                "request_id": row.request_id,
                "previous_hash": row.previous_hash,
                "event_hash": row.event_hash,
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
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    project_ids = session.exec(
        select(Project.id).where(Project.tenant_id == current_user.tenant_id)
    ).all()
    rows = session.exec(
        select(PromptAuditLog)
        .where(PromptAuditLog.project_id.in_(project_ids))
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
