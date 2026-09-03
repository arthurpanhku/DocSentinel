from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.core.config import settings
from app.core.db import get_session
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.governance import GateSubmission, GovernanceAuditLog
from app.models.user import User


def _override_session(engine):
    def _override():
        with Session(engine) as session:
            yield session

    return _override


def _seed_user(
    engine,
    *,
    role: str,
    is_superuser: bool = False,
    tenant_id: str = "default",
    username: str | None = None,
) -> User:
    with Session(engine) as session:
        user = User(
            username=username or f"{role}-user",
            email=f"{username or role}@example.com",
            hashed_password=get_password_hash("auth-test-pass"),
            role=role,
            is_active=True,
            is_superuser=is_superuser,
            tenant_id=tenant_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_write_api_auth_requires_token_and_roles(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    approved = tmp_path / "approved"
    approved.mkdir()
    monkeypatch.setattr(settings, "KB_REINDEX_ROOTS", str(approved))

    engine = create_engine(
        f"sqlite:///{tmp_path / 'auth.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    admin = _seed_user(engine, role="admin", is_superuser=True)
    basic = _seed_user(engine, role="user")
    app.dependency_overrides[get_session] = _override_session(engine)

    kb = MagicMock()
    kb.reindex_directory = AsyncMock(
        return_value={"directory": str(approved), "indexed": 0, "errors": []}
    )

    try:
        no_token = client.post(
            "/api/v1/kb/reindex",
            json={"directory": str(approved)},
        )
        assert no_token.status_code == 401

        with patch("app.api.kb.get_kb_service", return_value=kb):
            valid = client.post(
                "/api/v1/kb/reindex",
                json={"directory": str(approved)},
                headers={"Authorization": f"Bearer {create_access_token(admin.id)}"},
            )
        assert valid.status_code == 200
        assert valid.json()["indexed"] == 0

        insufficient = client.post(
            "/api/v1/kb/reindex",
            json={"directory": str(approved)},
            headers={"Authorization": f"Bearer {create_access_token(basic.id)}"},
        )
        assert insufficient.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_governance_tenant_boundary_and_authenticated_reviewer(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    engine = create_engine(
        f"sqlite:///{tmp_path / 'governance-auth.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    submitter = _seed_user(
        engine,
        role="client",
        tenant_id="tenant-a",
        username="submitter",
    )
    reviewer = _seed_user(
        engine,
        role="security_reviewer",
        tenant_id="tenant-a",
        username="reviewer",
    )
    outsider = _seed_user(
        engine,
        role="security_reviewer",
        tenant_id="tenant-b",
        username="outsider",
    )
    app.dependency_overrides[get_session] = _override_session(engine)
    submitter_headers = {"Authorization": f"Bearer {create_access_token(submitter.id)}"}
    reviewer_headers = {"Authorization": f"Bearer {create_access_token(reviewer.id)}"}
    outsider_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}

    try:
        assert client.get("/api/v1/projects").status_code == 401
        created = client.post(
            "/api/v1/projects",
            json={"name": "Tenant A project"},
            headers=submitter_headers,
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]

        hidden = client.get(
            f"/api/v1/projects/{project_id}",
            headers=outsider_headers,
        )
        assert hidden.status_code == 404

        invalid_transition = client.post(
            f"/api/v1/projects/{project_id}/gates/2/review",
            json={"status": "approved"},
            headers=reviewer_headers,
        )
        assert invalid_transition.status_code == 409

        submitted = client.post(
            f"/api/v1/projects/{project_id}/gates/1/submit",
            headers=submitter_headers,
        )
        assert submitted.status_code == 200

        reviewed = client.post(
            f"/api/v1/projects/{project_id}/gates/1/review",
            json={"status": "approved", "reviewed_by_id": submitter.id},
            headers=reviewer_headers,
        )
        assert reviewed.status_code == 200

        own_project = client.post(
            "/api/v1/projects",
            json={"name": "Reviewer-submitted project"},
            headers=reviewer_headers,
        ).json()["data"]["id"]
        assert (
            client.post(
                f"/api/v1/projects/{own_project}/gates/1/submit",
                headers=reviewer_headers,
            ).status_code
            == 200
        )
        self_review = client.post(
            f"/api/v1/projects/{own_project}/gates/1/review",
            json={"status": "approved"},
            headers=reviewer_headers,
        )
        assert self_review.status_code == 409

        with Session(engine) as session:
            submission = session.exec(
                select(GateSubmission).where(
                    GateSubmission.project_id == UUID(project_id),
                    GateSubmission.gate_number == 1,
                )
            ).one()
            assert submission.submitted_by_id == submitter.id
            assert submission.reviewed_by_id == reviewer.id
            logs = session.exec(
                select(GovernanceAuditLog)
                .where(GovernanceAuditLog.tenant_id == "tenant-a")
                .order_by(GovernanceAuditLog.created_at)
            ).all()
            assert len(logs) >= 3
            assert logs[-1].previous_hash == logs[-2].event_hash
    finally:
        app.dependency_overrides.clear()
