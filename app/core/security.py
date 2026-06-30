from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(subject: str | Any, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def ensure_role(user: Any, *roles: str) -> Any:
    """Return user when role is allowed, otherwise raise 403."""
    if getattr(user, "is_superuser", False):
        return user
    if getattr(user, "role", None) in set(roles):
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Requires one of roles: {sorted(set(roles))}",
    )


def require_roles(*roles: str):
    """Dependency-compatible role checker for governance APIs."""

    def _check(current_user: Any) -> Any:
        return ensure_role(current_user, *roles)

    return _check
