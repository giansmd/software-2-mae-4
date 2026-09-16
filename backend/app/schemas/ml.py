"""Pydantic schemas for the ML surrogate model endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.scenario import SeaLevelRise
from app.schemas.simulation import SimulationRequest
from app.simulations.engine import HYPOTHESIS_THRESHOLD


class RegressionMetrics(BaseModel):
    r2_variation: float
    mae_variation: float
    rmse_variation: float
    r2_carbon: float
    mae_carbon: float
    rmse_carbon: float
    cv_r2_mean: float
    cv_r2_std: float


class ClassificationMetrics(BaseModel):
    accuracy: float
    roc_auc: float


class MLMetadata(BaseModel):
    algorithm: str
    model_version: str
    data_source: str
    trained_at: str
    n_samples: int
    n_train: int
    n_test: int
    feature_names: list[str]
    feature_importances: dict[str, float]
    regression: RegressionMetrics
    classification: ClassificationMetrics


class MLPredictionRequest(SimulationRequest):
    """Same inputs as a simulation: either a scenario_id or inline parameters."""


class MLPredictionResult(BaseModel):
    scenario_id: Optional[int] = None
    scenario_name: str

    restoration_level: float
    sea_level_rise: SeaLevelRise
    horizon_year: int
    baseline_area_ha: float
    baseline_carbon_density: float

    # Surrogate prediction
    ml_variation_pct: float
    ml_horizon_carbon: float
    ml_meets_hypothesis: bool
    ml_meets_hypothesis_probability: float

    # Deterministic engine output, for side-by-side comparison
    engine_variation_pct: float
    engine_horizon_carbon: float
    engine_meets_hypothesis: bool

    delta_variation_pct: float
    hypothesis_threshold_pct: float = HYPOTHESIS_THRESHOLD
