"""Pydantic schemas for the user module."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    institution: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: Role = Role.VISITANTE


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    institution: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    institution: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    institution: Optional[str] = None
    role: Role
    is_active: bool
