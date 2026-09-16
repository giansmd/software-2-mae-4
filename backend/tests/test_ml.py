"""Tests for the ML surrogate model: dataset, training and endpoints."""
from __future__ import annotations

import numpy as np

from app.ml.train import train_model
from app.ml.dataset import FEATURE_NAMES, generate_dataset
from app.ml.registry import get_model, predict
from app.models.scenario import SeaLevelRise

HYPOTHESIS_THRESHOLD = 25.0


# ---------------------------------------------------------------------------
# Dataset generator (pure, reproducible, no database)
# ---------------------------------------------------------------------------


def test_dataset_is_deterministic_for_same_seed():
    a = generate_dataset(n_samples=200, seed=7)
    b = generate_dataset(n_samples=200, seed=7)
    assert np.array_equal(a.X, b.X)
    assert np.array_equal(a.y_regression, b.y_regression)
    assert np.array_equal(a.y_meets, b.y_meets)


def test_dataset_changes_with_seed():
    a = generate_dataset(n_samples=200, seed=1)
    b = generate_dataset(n_samples=200, seed=2)
    assert not np.array_equal(a.X, b.X)


def test_dataset_shape_and_feature_names():
    data = generate_dataset(n_samples=300, seed=3)
    assert data.X.shape == (300, len(FEATURE_NAMES))
    assert data.y_regression.shape == (300, 2)
    assert data.y_meets.shape == (300,)
    assert set(np.unique(data.y_meets)).issubset({0, 1})
    assert data.feature_names == list(FEATURE_NAMES)


def test_dataset_rejects_empty():
    import pytest

    with pytest.raises(ValueError):
        generate_dataset(n_samples=0)


# ---------------------------------------------------------------------------
# Training quality: the surrogate must emulate the engine closely
# ---------------------------------------------------------------------------


def test_trained_regressor_is_accurate():
    model = train_model(n_samples=2000)
    assert model.metadata["regression"]["r2_variation"] >= 0.9
    assert model.metadata["regression"]["r2_carbon"] >= 0.9
    assert model.metadata["classification"]["accuracy"] >= 0.9


def test_feature_importances_reported():
    model = train_model(n_samples=1500)
    importances = model.metadata["feature_importances"]
    assert set(importances) == set(FEATURE_NAMES)
    assert all(0.0 <= v <= 1.0 for v in importances.values())


# ---------------------------------------------------------------------------
# Prediction behaviour of the persisted/cached surrogate
# ---------------------------------------------------------------------------


def test_prediction_is_monotonic_in_restoration():
    low = predict(0.0, SeaLevelRise.MEDIUM, 2050, 120.0, 85.0)
    high = predict(90.0, SeaLevelRise.MEDIUM, 2050, 120.0, 85.0)
    assert high["variation_pct"] > low["variation_pct"]
    assert high["horizon_carbon"] > low["horizon_carbon"]


def test_prediction_tracks_engine_within_tolerance():
    """The emulator should stay close to the deterministic engine."""
    from app.simulations.engine import run_simulation

    samples = [(0.0, SeaLevelRise.HIGH), (50.0, SeaLevelRise.MEDIUM), (90.0, SeaLevelRise.LOW)]
    deltas = []
    for restoration, slr in samples:
        ml = predict(restoration, slr, 2050, 120.0, 85.0)
        engine = run_simulation(
            restoration_level=restoration,
            sea_level_rise=slr,
            horizon_year=2050,
            baseline_area_ha=120.0,
            baseline_carbon_density=85.0,
        )
        deltas.append(abs(ml["variation_pct"] - engine["horizon_variation_pct"]))
    assert max(deltas) < 8.0


def test_model_is_cached_between_calls():
    first = get_model()
    second = get_model()
    assert first is second


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------


def test_ml_metadata_endpoint(client):
    res = client.get("/api/ml/metadata")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["n_samples"] > 0
    assert "regression" in body and "classification" in body
    assert body["data_source"].startswith("synthetic")


def test_ml_predict_inline_params(client):
    res = client.post(
        "/api/ml/predict",
        json={
            "restoration_level": 90.0,
            "sea_level_rise": "low",
            "horizon_year": 2050,
            "baseline_area_ha": 120.0,
            "baseline_carbon_density": 85.0,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert "ml_variation_pct" in body
    assert "engine_variation_pct" in body
    assert body["hypothesis_threshold_pct"] == HYPOTHESIS_THRESHOLD


def test_ml_predict_requires_full_params_or_scenario(client):
    res = client.post("/api/ml/predict", json={"restoration_level": 50.0})
    assert res.status_code == 400


def test_ml_predict_public_scenario(client):
    scenarios = client.get("/api/scenarios").json()
    public = next(s for s in scenarios if s["is_public"])
    res = client.get(f"/api/ml/predict/{public['id']}")
    assert res.status_code == 200, res.text
    assert res.json()["scenario_id"] == public["id"]
