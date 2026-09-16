"""Lazy singleton that owns the trained surrogate model.

The model is loaded from disk on first use; if no artifact exists it is trained
deterministically from the engine and persisted. A lock keeps concurrent
requests from training twice.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

import numpy as np

from app.ml.dataset import SLR_ENCODING
from app.ml.train import ARTIFACT_PATH, TrainedModel, load_model, save_model, train_model
from app.models.scenario import SeaLevelRise

_lock = threading.Lock()
_model: Optional[TrainedModel] = None


def _build_and_save() -> TrainedModel:
    model = train_model()
    save_model(model)
    return model


def get_model(force_retrain: bool = False) -> TrainedModel:
    """Return the cached model, loading or training it on demand."""
    global _model
    if _model is not None and not force_retrain:
        return _model
    with _lock:
        if _model is None or force_retrain:
            if not force_retrain and ARTIFACT_PATH.exists():
                try:
                    _model = load_model()
                except Exception:  # noqa: BLE001 - corrupt/incompatible artifact
                    _model = _build_and_save()
            else:
                _model = _build_and_save()
    return _model


def get_metadata() -> dict[str, Any]:
    return dict(get_model().metadata)


def build_features(
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
) -> np.ndarray:
    return np.array(
        [
            [
                float(restoration_level),
                float(SLR_ENCODING[sea_level_rise]),
                float(horizon_year),
                float(baseline_area_ha),
                float(baseline_carbon_density),
            ]
        ],
        dtype=float,
    )


def predict(
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
) -> dict[str, float | bool]:
    """Predict the horizon variation, retained carbon and hypothesis outcome."""
    model = get_model()
    features = build_features(
        restoration_level=restoration_level,
        sea_level_rise=sea_level_rise,
        horizon_year=horizon_year,
        baseline_area_ha=baseline_area_ha,
        baseline_carbon_density=baseline_carbon_density,
    )
    variation_pct, horizon_carbon = (float(v) for v in model.regressor.predict(features)[0])
    meets = bool(model.classifier.predict(features)[0])
    meets_proba = float(model.classifier.predict_proba(features)[0][1])
    return {
        "variation_pct": round(variation_pct, 2),
        "horizon_carbon": round(horizon_carbon, 2),
        "meets_hypothesis": meets,
        "meets_hypothesis_probability": round(meets_proba, 4),
    }
