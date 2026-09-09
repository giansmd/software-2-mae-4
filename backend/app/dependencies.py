"""FastAPI dependencies: current user and role-based authorization."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import Role, User
from app.services.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_prefix}/auth/login", auto_error=False
)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise _credentials_error
    claims = decode_access_token(token)
    if claims is None:
        raise _credentials_error
    user = db.get(User, int(claims[0]))
    if user is None or not user.is_active:
        raise _credentials_error
    if claims[1] != user.token_version:  # SEC-002: token revocado tras cambiar contraseña
        raise _credentials_error
    return user


def get_optional_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of 401 for anonymous access."""
    if not token:
        return None
    claims = decode_access_token(token)
    if claims is None:
        return None
    user = db.get(User, int(claims[0]))
    if user is None or not user.is_active:
        return None
    if claims[1] != user.token_version:  # SEC-002: token revocado tras cambiar contraseña
        return None
    return user


def require_role(*roles: Role):
    """Dependency factory that restricts an endpoint to the given roles."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permiso insuficiente para este recurso",
            )
        return user

    return checker
