"""Reusable FastAPI dependencies for REST API authentication."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.core.security import decode_access_token, ensure_role
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AnonymousUser:
    id: int | None = None
    username: str = "local-dev"
    email: str | None = None
    full_name: str = "Local Development User"
    role: str = "admin"
    is_active: bool = True
    is_superuser: bool = True


def is_loopback_request(request: Request) -> bool:
    client = request.client
    if client is None:
        return False
    host = client.host
    if host in {"localhost", "testclient"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _unauthorized(detail: str = "Not authenticated.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _find_user(subject: str, session: Session) -> User | None:
    try:
        return session.get(User, int(subject))
    except (TypeError, ValueError):
        pass
    return session.exec(
        select(User).where((User.email == subject) | (User.username == subject))
    ).first()


def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> Any:
    if not settings.AUTH_ENABLED:
        if is_loopback_request(request):
            return AnonymousUser()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tokenless API access is loopback-only when auth is disabled.",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")
    if not subject:
        raise _unauthorized("Token subject is missing.")

    user = _find_user(str(subject), session)
    if user is None:
        raise _unauthorized("User not found.")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )
    return user


def require_roles(*roles: str):
    def _dependency(
        current_user: Annotated[Any, Depends(get_current_user)],
    ) -> Any:
        return ensure_role(current_user, *roles)

    return _dependency
