from __future__ import annotations

from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.core.security import ALGORITHM, create_access_token, verify_password
from app.models.user import User

from .utils import ok

router = APIRouter(prefix="/auth", tags=["governance-auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenRequest(BaseModel):
    token: str


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }


def _find_user(identifier: str, session: Session) -> User | None:
    return session.exec(
        select(User).where((User.email == identifier) | (User.username == identifier))
    ).first()


@router.post("/login")
async def login(
    payload: LoginRequest,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    user = _find_user(payload.email, session)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )
    return ok(
        {
            "access_token": create_access_token(user.id),
            "token_type": "bearer",
            "user": _serialize_user(user),
        }
    )


@router.post("/me")
async def me(
    payload: TokenRequest,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    try:
        decoded = jwt.decode(
            payload.token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id = int(decoded.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        ) from exc
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return ok(_serialize_user(user))
