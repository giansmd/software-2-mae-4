"""Security helpers: password hashing and JWT tokens."""
from __future__ import annotations

import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password (bcrypt, compatible with 3.x/4.x/5.x)."""
    pw = password.encode("utf-8")
    try:
        return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")
    except AttributeError:  # bcrypt >= 5 removed hashpw
        return bcrypt.hash(pw)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    pw = password.encode("utf-8")
    h = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(pw, h)
    except AttributeError:
        return bcrypt.check(pw, h)


def create_access_token(
    subject: str | int,
    expires_minutes: int | None = None,
    token_version: int = 0,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": str(subject), "exp": expire, "ver": token_version}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> tuple[str, int] | None:
    """Return ``(subject, token_version)`` or ``None`` if the token is invalid.

    Tokens signed before SEC-002 have no ``ver`` claim and are treated as
    version 0, so they stay valid until the user's password changes (which
    bumps ``users.token_version`` past 0).
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    sub = payload.get("sub")
    if sub is None or not str(sub).isdigit():
        return None
    ver = payload.get("ver", 0)
    if isinstance(ver, bool) or not isinstance(ver, int) or ver < 0:
        return None
    return str(sub), ver
