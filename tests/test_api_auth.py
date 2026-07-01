from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.core.config import settings
from app.core.db import get_session
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User


def _override_session(engine):
    def _override():
        with Session(engine) as session:
            yield session

    return _override


def _seed_user(engine, *, role: str, is_superuser: bool = False) -> User:
    with Session(engine) as session:
        user = User(
            username=f"{role}-user",
            email=f"{role}@example.com",
            hashed_password=get_password_hash("auth-test-pass"),
            role=role,
            is_active=True,
            is_superuser=is_superuser,
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
