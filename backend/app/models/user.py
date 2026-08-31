"""User model and role enum."""
from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    INVESTIGADOR = "INVESTIGADOR"
    VISITANTE = "VISITANTE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.VISITANTE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
