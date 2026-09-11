"""
Security utilities: JWT token creation/validation and password hashing.

Uses ``PyJWT`` for JWT operations and bcrypt for password hashing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import bcrypt
import jwt
from jwt import PyJWTError

from app.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    data:
        Claims to encode (must include ``"sub"`` for the user ID).
    expires_delta:
        Custom expiration duration. Defaults to
        ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return cast("str", jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM))


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a signed JWT refresh token with a longer expiry.

    Each token includes a unique ``jti`` (JWT ID) claim so that tokens
    generated with identical payloads in the same second are still distinct.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid4())})
    return cast("str", jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM))


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Raises
    ------
    ValueError
        If the token is invalid, expired, or cannot be decoded.
    """
    settings = get_settings()
    try:
        return cast("dict[str, Any]", jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM]))
    except PyJWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
