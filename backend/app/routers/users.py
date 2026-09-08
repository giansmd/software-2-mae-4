"""User administration endpoints (ADMIN only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _guard_admin_change(
    db: Session,
    target: User,
    current: User,
    *,
    role: Role | None = None,
    is_active: bool | None = None,
) -> None:
    """AUTH-002: prevent admin self-lockout and guarantee that at least one
    active ADMIN always remains in the system."""
    if target.id == current.id and (
        (role is not None and role != Role.ADMIN) or is_active is False
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No puedes degradar ni desactivar tu propia cuenta",
        )
    loses_admin = (
        target.role == Role.ADMIN
        and target.is_active
        and ((role is not None and role != Role.ADMIN) or is_active is False)
    )
    if loses_admin:
        other_active_admins = (
            db.query(User)
            .filter(
                User.role == Role.ADMIN,
                User.is_active.is_(True),
                User.id != target.id,
            )
            .count()
        )
        if other_active_admins == 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Debe quedar al menos un ADMIN activo en el sistema",
            )


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
) -> list[User]:
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        institution=payload.institution,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(Role.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    data = payload.model_dump(exclude_unset=True)
    _guard_admin_change(
        db,
        user,
        current,
        role=data.get("role"),
        is_active=data.get("is_active"),
    )
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(Role.ADMIN)),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    _guard_admin_change(db, user, current, is_active=False)
    user.is_active = False
    db.commit()
