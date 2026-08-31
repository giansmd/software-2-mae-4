"""Pydantic schemas for simulation results."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.scenario import SeaLevelRise


class SimulationRequest(BaseModel):
    """Run a simulation either for an existing scenario or from inline parameters."""
    scenario_id: Optional[int] = None
    restoration_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    sea_level_rise: Optional[SeaLevelRise] = None
    horizon_year: Optional[int] = Field(None, ge=2026, le=2125)
    baseline_area_ha: Optional[float] = Field(None, gt=0)
    baseline_carbon_density: Optional[float] = Field(None, gt=0)
    scenario_name: Optional[str] = None


class SeriesPoint(BaseModel):
    year: int
    retained_carbon: float
    effective_area_ha: float
    vegetation_cover: float
    variation_pct: float


class SimulationResult(BaseModel):
    scenario_id: Optional[int] = None
    scenario_name: str
    restoration_level: float
    sea_level_rise: SeaLevelRise
    horizon_year: int
    baseline_area_ha: float
    baseline_carbon_density: float
    baseline_carbon: float
    horizon_carbon: float
    horizon_variation_pct: float
    meets_hypothesis: bool
    hypothesis_threshold_pct: float = 25.0
    series: list[SeriesPoint]
