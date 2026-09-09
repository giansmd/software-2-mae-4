"""Authentication endpoints: register, login (JWT), profile."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import PasswordChange, ProfileUpdate, UserOut
from app.services.rate_limit import FixedWindowLimiter, enforce
from app.services.security import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# SEC-004: per-IP budgets to slow down brute force and registration spam.
# The limiters are module singletons built from settings; tests may replace
# them to exercise the 429 path.
LOGIN_LIMITER = FixedWindowLimiter(
    limit=settings.login_rate_limit,
    window_seconds=settings.login_rate_window_minutes * 60,
)
REGISTER_LIMITER = FixedWindowLimiter(
    limit=settings.register_rate_limit,
    window_seconds=settings.register_rate_window_minutes * 60,
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    enforce(REGISTER_LIMITER, request, "registro")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        institution=payload.institution,
        role=Role.VISITANTE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(
        access_token=create_access_token(user.id, token_version=user.token_version),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    enforce(LOGIN_LIMITER, request, "inicio de sesión")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password) or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
    return Token(
        access_token=create_access_token(user.id, token_version=user.token_version),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.put("/me", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None and payload.email != user.email:
        if db.query(User).filter(User.email == payload.email, User.id != user.id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está en uso")
        user.email = payload.email
    if payload.institution is not None:
        user.institution = payload.institution
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Contraseña actual incorrecta")
    user.hashed_password = hash_password(payload.new_password)
    user.token_version += 1  # SEC-002: invalida todos los JWT emitidos hasta ahora
    db.commit()
