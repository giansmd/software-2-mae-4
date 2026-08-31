"""Unit tests for the carbon retention simulation engine."""
from __future__ import annotations

from app.models.scenario import SeaLevelRise
from app.simulations.engine import run_simulation


def test_high_restoration_retains_more_than_low():
    """High restoration must retain more carbon at the horizon than no restoration."""
    base = dict(
        sea_level_rise=SeaLevelRise.MEDIUM,
        horizon_year=2050,
        baseline_area_ha=120.0,
        baseline_carbon_density=85.0,
    )
    low = run_simulation(restoration_level=0.0, **base)
    high = run_simulation(restoration_level=90.0, **base)
    assert high["horizon_carbon"] > low["horizon_carbon"]


def test_high_restoration_low_slr_meets_hypothesis():
    """Restauración alta + SLR bajo should reach >= +25% vs baseline (the thesis)."""
    result = run_simulation(
        restoration_level=90.0,
        sea_level_rise=SeaLevelRise.LOW,
        horizon_year=2050,
        baseline_area_ha=120.0,
        baseline_carbon_density=85.0,
    )
    assert result["horizon_variation_pct"] >= 25.0
    assert result["meets_hypothesis"] is True


def test_no_restoration_does_not_meet_hypothesis():
    result = run_simulation(
        restoration_level=0.0,
        sea_level_rise=SeaLevelRise.HIGH,
        horizon_year=2050,
        baseline_area_ha=120.0,
        baseline_carbon_density=85.0,
    )
    assert result["horizon_variation_pct"] < 25.0
    assert result["meets_hypothesis"] is False


def test_sea_level_rise_reduces_retention():
    base = dict(restoration_level=0.0, horizon_year=2050, baseline_area_ha=120.0, baseline_carbon_density=85.0)
    low = run_simulation(sea_level_rise=SeaLevelRise.LOW, **base)
    high = run_simulation(sea_level_rise=SeaLevelRise.HIGH, **base)
    assert high["horizon_carbon"] < low["horizon_carbon"]
