"""Carbon retention simulation engine (the scientific core of the prototype).

Modelo explicable de retención de carbono azul en un humedal costero:

  Línea base (año inicial):  C0 = A0 * D0
      A0 = superficie efectiva del humedal (ha)
      D0 = densidad de carbono del suelo + biomasa (tC/ha)

  Con restauración hidrológica (nivel R en 0..1):
      factor_restauracion = Bmax * (1 - exp(-k * R))
      -> curva saturante: a mayor R, menor ganancia marginal (ley de
         rendimientos decrecientes). La productividad del humedal sube pero
         se satura.
      densidad(t) = D0 * (1 + factor_restauracion)

  Con subida del nivel del mar (escenario SLR):
      area_efectiva(t) = A0 * (1 - perdida_area(SLR) * frac)
      densidad(t)     = D0 * (...) * (1 - perdida_densidad(SLR) * frac)
      donde frac = (año - año_inicial) / (horizonte - año_inicial)
      -> la superficie se pierde progresivamente (inundación/salinización) y
         la densidad de carbono decae, con mayor impacto en escenarios altos.

  Retenido(t) = area_efectiva(t) * densidad(t)

  Variación % vs línea base = (Retenido(t) - C0) / C0 * 100
  Hipótesis del trabajo: restauración >= +25% de retención a 2050.
"""
from __future__ import annotations

import math
from typing import Optional

from app.models.scenario import SeaLevelRise

HYPOTHESIS_THRESHOLD = 25.0

# Default calibration parameters (overridable from the model_params table).
DEFAULT_PARAMS: dict[str, float] = {
    "start_year": 2025.0,
    "restoration_boost_max": 0.50,  # ganancia máxima de densidad a restauración total
    "restoration_k": 2.5,           # pendiente de la curva saturante
    "slr_area_loss_low": 0.06,      # fracción de área perdida al 2050 (IPCC bajo)
    "slr_area_loss_medium": 0.12,   # IPCC medio
    "slr_area_loss_high": 0.22,     # IPCC alto
    "slr_density_loss_low": 0.05,
    "slr_density_loss_medium": 0.12,
    "slr_density_loss_high": 0.20,
}

_SLR_KEYS = {
    SeaLevelRise.LOW: ("slr_area_loss_low", "slr_density_loss_low"),
    SeaLevelRise.MEDIUM: ("slr_area_loss_medium", "slr_density_loss_medium"),
    SeaLevelRise.HIGH: ("slr_area_loss_high", "slr_density_loss_high"),
}


def run_simulation(
    *,
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    params: Optional[dict[str, float]] = None,
    scenario_id: Optional[int] = None,
    scenario_name: str = "Escenario",
) -> dict:
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)

    start_year = int(p["start_year"])
    baseline_carbon = baseline_area_ha * baseline_carbon_density

    span = max(1, horizon_year - start_year)
    series: list[dict] = []
    for year in range(start_year, horizon_year + 1):
        frac = (year - start_year) / span
        point = calculate_state(
            restoration_level=restoration_level,
            sea_level_rise=sea_level_rise,
            progress=frac,
            baseline_area_ha=baseline_area_ha,
            baseline_carbon_density=baseline_carbon_density,
            params=p,
        )
        series.append(
            {
                "year": year,
                **point,
            }
        )

    horizon = series[-1]
    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "restoration_level": restoration_level,
        "sea_level_rise": sea_level_rise,
        "horizon_year": horizon_year,
        "baseline_area_ha": baseline_area_ha,
        "baseline_carbon_density": baseline_carbon_density,
        "baseline_carbon": round(baseline_carbon, 2),
        "horizon_carbon": horizon["retained_carbon"],
        "horizon_variation_pct": horizon["variation_pct"],
        "meets_hypothesis": horizon["variation_pct"] >= HYPOTHESIS_THRESHOLD,
        "hypothesis_threshold_pct": HYPOTHESIS_THRESHOLD,
        "series": series,
    }


def calculate_state(
    *,
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    progress: float,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    params: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """Calculate one state along the same projection curve used by the engine.

    ``progress`` is a normalized value between 0 and 1.  Keeping this operation
    separate lets the realtime stream reuse the scientific equations without
    generating a complete annual series for every websocket tick.
    """
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)

    R = max(0.0, min(100.0, restoration_level)) / 100.0
    boost_max = float(p["restoration_boost_max"])
    k = float(p["restoration_k"])
    area_loss_key, density_loss_key = _SLR_KEYS[sea_level_rise]
    slr_area_loss = float(p[area_loss_key])
    slr_density_loss = float(p[density_loss_key])
    frac = max(0.0, min(1.0, progress))

    baseline_carbon = baseline_area_ha * baseline_carbon_density
    restoration_factor = boost_max * (1.0 - math.exp(-k * R))
    effective_area = baseline_area_ha * (1.0 - slr_area_loss * frac)
    density = (
        baseline_carbon_density
        * (1.0 + restoration_factor)
        * (1.0 - slr_density_loss * frac)
    )
    retained = effective_area * density
    variation_pct = (
        (retained - baseline_carbon) / baseline_carbon * 100.0
        if baseline_carbon
        else 0.0
    )
    vegetation_cover = min(1.0, 0.6 + 0.4 * R * (1.0 - math.exp(-k * R)))
    return {
        "retained_carbon": round(retained, 2),
        "effective_area_ha": round(effective_area, 2),
        "vegetation_cover": round(vegetation_cover, 4),
        "variation_pct": round(variation_pct, 2),
    }
