from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt as bcrypt_backend
from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _bcrypt_secret(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def _bcrypt_hash(password: str) -> str:
    return bcrypt_backend.hashpw(
        _bcrypt_secret(password),
        bcrypt_backend.gensalt(),
    ).decode("utf-8")


def _bcrypt_verify(plain_password: str, hashed_password: str) -> bool:
    with suppress(ValueError, TypeError):
        return bcrypt_backend.checkpw(
            _bcrypt_secret(plain_password),
            hashed_password.encode("utf-8"),
        )
    return False


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
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return _bcrypt_verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except ValueError:
        return _bcrypt_hash(password)


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
