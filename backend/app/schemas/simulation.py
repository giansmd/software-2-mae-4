"""Pydantic schemas for simulation results."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.scenario import SeaLevelRise

PredictionMethod = Literal["engine", "ml", "ensemble"]


class SimulationRequest(BaseModel):
    """Run a simulation either for an existing scenario or from inline parameters."""
    scenario_id: Optional[int] = None
    restoration_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    sea_level_rise: Optional[SeaLevelRise] = None
    horizon_year: Optional[int] = Field(None, ge=2026, le=2125)
    baseline_area_ha: Optional[float] = Field(None, gt=0)
    baseline_carbon_density: Optional[float] = Field(None, gt=0)
    scenario_name: Optional[str] = None
    # Prediction source: deterministic engine (default), ML surrogate or hybrid.
    method: PredictionMethod = "engine"


class SeriesPoint(BaseModel):
    year: int
    retained_carbon: float
    effective_area_ha: float
    vegetation_cover: float
    variation_pct: float


class SimulationResult(BaseModel):
    scenario_id: Optional[int] = None
    scenario_name: str
    method: PredictionMethod = "engine"
    restoration_level: float
    sea_level_rise: SeaLevelRise
    horizon_year: int
    baseline_area_ha: float
    baseline_carbon_density: float
    baseline_carbon: float
    # Headline values come from the selected method.
    horizon_carbon: float
    horizon_variation_pct: float
    meets_hypothesis: bool
    hypothesis_threshold_pct: float = 25.0
    # Side-by-side comparison with the deterministic engine.
    engine_horizon_variation_pct: float
    engine_horizon_carbon: float
    engine_meets_hypothesis: bool
    # ``None`` when the selected method did not involve the ML model.
    ml_horizon_variation_pct: Optional[float] = None
    ml_horizon_carbon: Optional[float] = None
    ml_meets_hypothesis: Optional[bool] = None
    series: list[SeriesPoint]
