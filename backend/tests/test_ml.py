"""Tests for the ML surrogate model: dataset, training and endpoints."""
from __future__ import annotations

import struct

import numpy as np
import pandas as pd
import pytest

from app.ml.dataset import (
    FEATURE_NAMES,
    SERIES_FEATURE_NAMES,
    SERIES_TARGET_NAMES,
    generate_dataset,
    generate_series_dataset,
)
from app.ml.crispdm import fig_gmw_trend
from app.ml.registry import get_model, predict, predict_series
from app.ml.train import train_model
from app.models.scenario import SeaLevelRise
from app.simulations.engine import run_simulation

HYPOTHESIS_THRESHOLD = 25.0


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ---------------------------------------------------------------------------
# Dataset generators (pure, reproducible, no database)
# ---------------------------------------------------------------------------


def test_scenario_dataset_is_deterministic_for_same_seed():
    a = generate_dataset(n_samples=200, seed=7)
    b = generate_dataset(n_samples=200, seed=7)
    assert np.array_equal(a.X, b.X)
    assert np.array_equal(a.y_regression, b.y_regression)
    assert np.array_equal(a.y_meets, b.y_meets)


def test_scenario_dataset_changes_with_seed():
    a = generate_dataset(n_samples=200, seed=1)
    b = generate_dataset(n_samples=200, seed=2)
    assert not np.array_equal(a.X, b.X)


def test_scenario_dataset_shape_and_feature_names():
    data = generate_dataset(n_samples=300, seed=3)
    assert data.X.shape == (300, len(FEATURE_NAMES))
    assert data.y_regression.shape == (300, 2)
    assert data.y_meets.shape == (300,)
    assert set(np.unique(data.y_meets)).issubset({0, 1})
    assert data.feature_names == list(FEATURE_NAMES)


def test_scenario_dataset_rejects_empty():
    with pytest.raises(ValueError):
        generate_dataset(n_samples=0)


def test_series_dataset_is_deterministic_and_shaped():
    a = generate_series_dataset(n_scenarios=40, progress_per_scenario=8, seed=5)
    b = generate_series_dataset(n_scenarios=40, progress_per_scenario=8, seed=5)
    assert np.array_equal(a.X, b.X)
    assert np.array_equal(a.Y, b.Y)
    assert a.X.shape == (320, len(SERIES_FEATURE_NAMES))
    assert a.Y.shape == (320, len(SERIES_TARGET_NAMES))
    assert a.feature_names == list(SERIES_FEATURE_NAMES)
    assert a.target_names == list(SERIES_TARGET_NAMES)
    # progress is always within [0, 1] and both endpoints are present.
    progress = a.X[:, SERIES_FEATURE_NAMES.index("progress")]
    assert progress.min() == 0.0
    assert progress.max() == 1.0


def test_series_dataset_progress_1_matches_horizon_engine():
    data = generate_series_dataset(n_scenarios=20, progress_per_scenario=6, seed=11)
    idx = SERIES_FEATURE_NAMES.index("progress")
    var = SERIES_TARGET_NAMES.index("variation_pct")
    for row in range(data.X.shape[0]):
        if data.X[row, idx] != 1.0:
            continue
        rest = data.X[row, SERIES_FEATURE_NAMES.index("restoration_level")]
        code = data.X[row, SERIES_FEATURE_NAMES.index("sea_level_rise")]
        horizon = int(data.X[row, SERIES_FEATURE_NAMES.index("horizon_year")])
        slr = {0.0: SeaLevelRise.LOW, 1.0: SeaLevelRise.MEDIUM, 2.0: SeaLevelRise.HIGH}[code]
        engine = run_simulation(
            restoration_level=float(rest),
            sea_level_rise=slr,
            horizon_year=horizon,
            baseline_area_ha=float(data.X[row, SERIES_FEATURE_NAMES.index("baseline_area_ha")]),
            baseline_carbon_density=float(data.X[row, SERIES_FEATURE_NAMES.index("baseline_carbon_density")]),
        )
        assert data.Y[row, var] == pytest.approx(engine["horizon_variation_pct"], abs=0.05)


def test_exported_figure_is_complete_png_with_600_dpi_metadata():
    image = fig_gmw_trend(
        pd.DataFrame({"anio": [1996, 2020], "extension_ha": [3500, 4000]})
    )
    assert image.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    while offset < len(image):
        length = struct.unpack_from(">I", image, offset)[0]
        chunk_type = image[offset + 4 : offset + 8]
        if chunk_type == b"pHYs":
            x_ppm, y_ppm, unit = struct.unpack_from(">IIB", image, offset + 8)
            assert unit == 1
            assert x_ppm == y_ppm == round(600 / 0.0254)
            return
        offset += length + 12
    pytest.fail("PNG missing physical resolution metadata")


# ---------------------------------------------------------------------------
# Training quality
# ---------------------------------------------------------------------------


def test_trained_surrogate_is_accurate():
    model = train_model(n_scenarios=300, progress_per_scenario=12, n_samples=500)
    assert model.metadata["regression"]["r2_variation"] >= 0.85
    assert model.metadata["regression"]["r2_carbon"] >= 0.9
    assert model.metadata["classification"]["accuracy"] >= 0.9


def test_feature_importances_reported():
    model = train_model(n_scenarios=200, progress_per_scenario=10, n_samples=400)
    importances = model.metadata["feature_importances"]
    assert set(importances) == set(SERIES_FEATURE_NAMES)
    assert all(0.0 <= v <= 1.0 for v in importances.values())
    assert set(model.metadata["regression"]["per_target"]) == set(SERIES_TARGET_NAMES)


# ---------------------------------------------------------------------------
# Prediction behaviour of the cached model
# ---------------------------------------------------------------------------


def test_prediction_is_monotonic_in_restoration():
    low = predict(0.0, SeaLevelRise.MEDIUM, 2050, 120.0, 85.0)
    high = predict(90.0, SeaLevelRise.MEDIUM, 2050, 120.0, 85.0)
    assert high["variation_pct"] > low["variation_pct"]
    assert high["horizon_carbon"] > low["horizon_carbon"]


def test_prediction_tracks_engine_within_tolerance():
    """The emulator should stay close to the deterministic engine."""
    samples = [0.0, 50.0, 90.0]
    slrs = [SeaLevelRise.HIGH, SeaLevelRise.MEDIUM, SeaLevelRise.LOW]
    for restoration, slr in zip(samples, slrs):
        ml = predict(restoration, slr, 2050, 120.0, 85.0)
        engine = run_simulation(
            restoration_level=restoration,
            sea_level_rise=slr,
            horizon_year=2050,
            baseline_area_ha=120.0,
            baseline_carbon_density=85.0,
        )
        assert abs(ml["variation_pct"] - engine["horizon_variation_pct"]) < 8.0


def test_predict_series_covers_every_year():
    series = predict_series(60.0, SeaLevelRise.MEDIUM, 2050, 120.0, 85.0, start_year=2025)
    assert [int(p["year"]) for p in series] == list(range(2025, 2051))
    assert all("retained_carbon" in p for p in series)


def test_model_is_cached_between_calls():
    assert get_model() is get_model()


# ---------------------------------------------------------------------------
# HTTP endpoints: ML module
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


# ---------------------------------------------------------------------------
# HTTP endpoints: prediction method selector (engine / ml / ensemble)
# ---------------------------------------------------------------------------


INLINE = {
    "restoration_level": 90.0,
    "sea_level_rise": "low",
    "horizon_year": 2050,
    "baseline_area_ha": 120.0,
    "baseline_carbon_density": 85.0,
}


@pytest.mark.parametrize("method", ["engine", "ml", "ensemble"])
def test_simulation_method_selector(client, method):
    res = client.post("/api/simulations/run", json={**INLINE, "method": method})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["method"] == method
    assert len(body["series"]) == 26  # 2025..2050
    assert body["hypothesis_threshold_pct"] == HYPOTHESIS_THRESHOLD
    if method == "engine":
        assert body["ml_horizon_variation_pct"] is None
    else:
        assert body["ml_horizon_variation_pct"] is not None
        assert body["ml_meets_hypothesis"] is not None


def test_engine_method_matches_raw_engine(client):
    res = client.post("/api/simulations/run", json={**INLINE, "method": "engine"})
    body = res.json()
    engine = run_simulation(
        restoration_level=INLINE["restoration_level"],
        sea_level_rise=SeaLevelRise.LOW,
        horizon_year=INLINE["horizon_year"],
        baseline_area_ha=INLINE["baseline_area_ha"],
        baseline_carbon_density=INLINE["baseline_carbon_density"],
    )
    assert body["horizon_variation_pct"] == pytest.approx(
        engine["horizon_variation_pct"], abs=0.01
    )
    assert body["engine_horizon_variation_pct"] == pytest.approx(
        engine["horizon_variation_pct"], abs=0.01
    )


def test_ensemble_stays_between_engine_and_ml(client):
    engine = client.post("/api/simulations/run", json={**INLINE, "method": "engine"}).json()
    ml = client.post("/api/simulations/run", json={**INLINE, "method": "ml"}).json()
    ens = client.post("/api/simulations/run", json={**INLINE, "method": "ensemble"}).json()
    low = min(engine["horizon_variation_pct"], ml["horizon_variation_pct"])
    high = max(engine["horizon_variation_pct"], ml["horizon_variation_pct"])
    assert low - 0.5 <= ens["horizon_variation_pct"] <= high + 0.5


def test_invalid_method_is_rejected(client):
    res = client.post("/api/simulations/run", json={**INLINE, "method": "magic"})
    assert res.status_code == 422


def test_simulation_get_accepts_method(client):
    public = next(s for s in client.get("/api/scenarios").json() if s["is_public"])
    res = client.get(f"/api/simulations/{public['id']}?method=ml")
    assert res.status_code == 200, res.text
    assert res.json()["method"] == "ml"


@pytest.mark.parametrize("fmt", ["pdf", "docx", "xlsx"])
def test_reports_support_ml_method(client, fmt):
    token = _login(client, "inv@mae4.dev", "Invest12345")
    public = next(s for s in client.get("/api/scenarios").json() if s["is_public"])
    res = client.get(
        f"/api/reports/{public['id']}/{fmt}?method=ensemble",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    assert len(res.content) > 100
