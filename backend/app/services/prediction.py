"""Prediction orchestration: deterministic engine, ML surrogate or ensemble.

Centralising this keeps the simulation and report routers from duplicating the
engine call and makes the ``method`` selector a single place to evolve.
"""
from __future__ import annotations

from typing import Optional

from app.config import settings
from app.ml import registry
from app.models.scenario import SeaLevelRise
from app.simulations.engine import HYPOTHESIS_THRESHOLD, run_simulation

VALID_METHODS = ("engine", "ml", "ensemble")

METHOD_LABELS: dict[str, str] = {
    "engine": "Motor determinista",
    "ml": "Modelo de IA",
    "ensemble": "Ensemble (motor + IA)",
}


class PredictionUnavailableError(RuntimeError):
    """Raised when a method needs the ML model but it is disabled."""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def predict_scenario(
    *,
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    params: Optional[dict[str, float]] = None,
    method: str = "engine",
    scenario_id: Optional[int] = None,
    scenario_name: str = "Escenario",
) -> dict:
    """Run the requested prediction method and return a ``SimulationResult`` dict."""
    if method not in VALID_METHODS:
        raise ValueError(
            f"method inválido: {method!r}; use uno de {VALID_METHODS}"
        )

    engine = run_simulation(
        restoration_level=restoration_level,
        sea_level_rise=sea_level_rise,
        horizon_year=horizon_year,
        baseline_area_ha=baseline_area_ha,
        baseline_carbon_density=baseline_carbon_density,
        params=params,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
    )
    start_year = int((params or {}).get("start_year", 2025))

    ml_summary: Optional[dict] = None
    if method == "engine":
        series = engine["series"]
        headline_variation = engine["horizon_variation_pct"]
        headline_carbon = engine["horizon_carbon"]
        headline_meets = engine["meets_hypothesis"]
    else:
        if not settings.ml_enabled:
            raise PredictionUnavailableError(
                "El modelo de IA está deshabilitado (ML_ENABLED=false); "
                "use method=engine o habilite el módulo"
            )
        ml_series = registry.predict_series(
            restoration_level=restoration_level,
            sea_level_rise=sea_level_rise,
            horizon_year=horizon_year,
            baseline_area_ha=baseline_area_ha,
            baseline_carbon_density=baseline_carbon_density,
            start_year=start_year,
        )
        ml_pred = registry.predict(
            restoration_level=restoration_level,
            sea_level_rise=sea_level_rise,
            horizon_year=horizon_year,
            baseline_area_ha=baseline_area_ha,
            baseline_carbon_density=baseline_carbon_density,
            start_year=start_year,
        )
        ml_summary = {
            "variation_pct": ml_pred["variation_pct"],
            "horizon_carbon": ml_pred["horizon_carbon"],
            "meets_hypothesis": ml_pred["meets_hypothesis"],
        }

        if method == "ml":
            series = ml_series
            headline_variation = ml_pred["variation_pct"]
            headline_carbon = ml_pred["horizon_carbon"]
            headline_meets = ml_pred["meets_hypothesis"]
        else:  # ensemble
            weight = _clamp(settings.ensemble_weight, 0.0, 1.0)
            series = [
                {
                    "year": e["year"],
                    "retained_carbon": round(
                        weight * e["retained_carbon"]
                        + (1 - weight) * m["retained_carbon"],
                        2,
                    ),
                    "effective_area_ha": round(
                        weight * e["effective_area_ha"]
                        + (1 - weight) * m["effective_area_ha"],
                        2,
                    ),
                    "vegetation_cover": round(
                        weight * e["vegetation_cover"]
                        + (1 - weight) * m["vegetation_cover"],
                        4,
                    ),
                    "variation_pct": round(
                        weight * e["variation_pct"]
                        + (1 - weight) * m["variation_pct"],
                        2,
                    ),
                }
                for e, m in zip(engine["series"], ml_series)
            ]
            headline_variation = round(
                weight * engine["horizon_variation_pct"]
                + (1 - weight) * ml_pred["variation_pct"],
                2,
            )
            headline_carbon = round(
                weight * engine["horizon_carbon"]
                + (1 - weight) * ml_pred["horizon_carbon"],
                2,
            )
            headline_meets = headline_variation >= HYPOTHESIS_THRESHOLD

    return {
        "scenario_id": engine["scenario_id"],
        "scenario_name": engine["scenario_name"],
        "method": method,
        "restoration_level": engine["restoration_level"],
        "sea_level_rise": engine["sea_level_rise"],
        "horizon_year": engine["horizon_year"],
        "baseline_area_ha": engine["baseline_area_ha"],
        "baseline_carbon_density": engine["baseline_carbon_density"],
        "baseline_carbon": engine["baseline_carbon"],
        "horizon_carbon": headline_carbon,
        "horizon_variation_pct": headline_variation,
        "meets_hypothesis": headline_meets,
        "hypothesis_threshold_pct": engine["hypothesis_threshold_pct"],
        "engine_horizon_variation_pct": engine["horizon_variation_pct"],
        "engine_horizon_carbon": engine["horizon_carbon"],
        "engine_meets_hypothesis": engine["meets_hypothesis"],
        "ml_horizon_variation_pct": (
            ml_summary["variation_pct"] if ml_summary else None
        ),
        "ml_horizon_carbon": ml_summary["horizon_carbon"] if ml_summary else None,
        "ml_meets_hypothesis": (
            ml_summary["meets_hypothesis"] if ml_summary else None
        ),
        "series": series,
    }
