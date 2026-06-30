from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.core.db import get_session
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User


def _override_session(engine):
    def _override():
        with Session(engine) as session:
            yield session

    return _override


def test_governance_jwt_login_round_trip(client, tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'phase6.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            User(
                username="phase6-admin",
                email="admin@example.com",
                full_name="Phase 6 Admin",
                hashed_password=get_password_hash("phase6-pass"),
                role="admin",
                is_active=True,
                is_superuser=True,
            )
        )
        session.commit()

    app.dependency_overrides[get_session] = _override_session(engine)
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "phase6-pass"},
        )
        assert response.status_code == 200
        session_data = response.json()["data"]
        assert session_data["token_type"] == "bearer"
        assert session_data["user"]["role"] == "admin"

        me = client.post(
            "/api/v1/auth/me",
            json={"token": session_data["access_token"]},
        )
        assert me.status_code == 200
        assert me.json()["data"]["email"] == "admin@example.com"
    finally:
        app.dependency_overrides.clear()
