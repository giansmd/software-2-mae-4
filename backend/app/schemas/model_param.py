"""Pydantic schemas for model calibration parameters."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ModelParamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None


class ModelParamUpdate(BaseModel):
    value: float
