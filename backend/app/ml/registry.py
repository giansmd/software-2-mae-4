"""Lazy singleton that owns the trained surrogate models.

The models are loaded from disk on first use; if no artifact exists they are
trained deterministically from the engine and persisted. A lock keeps
concurrent requests from training twice.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

import numpy as np

from app.ml.dataset import SLR_ENCODING, SERIES_TARGET_NAMES
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
    """Scenario-level feature row (classifier input)."""
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


def build_series_features(
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    progresses: list[float],
) -> np.ndarray:
    """Per-year feature matrix for the series regressor."""
    slr = float(SLR_ENCODING[sea_level_rise])
    return np.array(
        [
            [
                float(restoration_level),
                slr,
                float(horizon_year),
                float(baseline_area_ha),
                float(baseline_carbon_density),
                float(p),
            ]
            for p in progresses
        ],
        dtype=float,
    )


def predict_series(
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    start_year: int,
) -> list[dict[str, float]]:
    """Predict the full annual curve, one row per year in [start, horizon]."""
    span = max(1, horizon_year - start_year)
    progresses = [(year - start_year) / span for year in range(start_year, horizon_year + 1)]
    features = build_series_features(
        restoration_level=restoration_level,
        sea_level_rise=sea_level_rise,
        horizon_year=horizon_year,
        baseline_area_ha=baseline_area_ha,
        baseline_carbon_density=baseline_carbon_density,
        progresses=progresses,
    )
    predictions = get_model().series_regressor.predict(features)
    targets = {name: i for i, name in enumerate(SERIES_TARGET_NAMES)}
    series: list[dict[str, float]] = []
    for offset, year in enumerate(range(start_year, horizon_year + 1)):
        row = predictions[offset]
        series.append(
            {
                "year": float(year),
                "retained_carbon": round(float(row[targets["retained_carbon"]]), 2),
                "effective_area_ha": round(float(row[targets["effective_area_ha"]]), 2),
                "vegetation_cover": round(
                    max(0.0, min(1.0, float(row[targets["vegetation_cover"]]))), 4
                ),
                "variation_pct": round(float(row[targets["variation_pct"]]), 2),
            }
        )
    return series


def predict(
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    start_year: int = 2025,
) -> dict[str, float | bool]:
    """Predict the horizon variation, retained carbon and hypothesis outcome."""
    model = get_model()
    series = predict_series(
        restoration_level=restoration_level,
        sea_level_rise=sea_level_rise,
        horizon_year=horizon_year,
        baseline_area_ha=baseline_area_ha,
        baseline_carbon_density=baseline_carbon_density,
        start_year=start_year,
    )
    horizon = series[-1]
    features = build_features(
        restoration_level=restoration_level,
        sea_level_rise=sea_level_rise,
        horizon_year=horizon_year,
        baseline_area_ha=baseline_area_ha,
        baseline_carbon_density=baseline_carbon_density,
    )
    meets = bool(model.classifier.predict(features)[0])
    meets_proba = float(model.classifier.predict_proba(features)[0][1])
    return {
        "variation_pct": horizon["variation_pct"],
        "horizon_carbon": horizon["retained_carbon"],
        "meets_hypothesis": meets,
        "meets_hypothesis_probability": round(meets_proba, 4),
    }
