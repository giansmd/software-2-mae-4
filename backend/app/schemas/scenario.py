"""Pydantic schemas for scenarios."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.scenario import SeaLevelRise


class ScenarioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    restoration_level: float = Field(..., ge=0.0, le=100.0)
    sea_level_rise: SeaLevelRise = SeaLevelRise.MEDIUM
    horizon_year: int = Field(2050, ge=2026, le=2125)
    baseline_area_ha: float = Field(120.0, gt=0)
    baseline_carbon_density: float = Field(85.0, gt=0)
    is_public: bool = False


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    restoration_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    sea_level_rise: Optional[SeaLevelRise] = None
    horizon_year: Optional[int] = Field(None, ge=2026, le=2125)
    baseline_area_ha: Optional[float] = Field(None, gt=0)
    baseline_carbon_density: Optional[float] = Field(None, gt=0)
    is_public: Optional[bool] = None


class ScenarioOut(ScenarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: Optional[int] = None
