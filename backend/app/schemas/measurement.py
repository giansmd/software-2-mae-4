"""Pydantic schemas for measurements / samples."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MeasurementBase(BaseModel):
    date: date
    vegetation_cover: float = Field(..., ge=0.0)
    water_table: float
    soil_organic_carbon: float = Field(..., ge=0.0)
    biomass: float = Field(..., ge=0.0)
    note: Optional[str] = None


class MeasurementCreate(MeasurementBase):
    scenario_id: Optional[int] = None


class MeasurementUpdate(BaseModel):
    date: Optional[date] = None
    vegetation_cover: Optional[float] = Field(None, ge=0.0)
    water_table: Optional[float] = None
    soil_organic_carbon: Optional[float] = Field(None, ge=0.0)
    biomass: Optional[float] = Field(None, ge=0.0)
    note: Optional[str] = None
    scenario_id: Optional[int] = None


class MeasurementOut(MeasurementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_id: Optional[int] = None
    owner_id: Optional[int] = None
