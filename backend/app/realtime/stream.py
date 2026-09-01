"""Synthetic realtime stream built on top of the deterministic model."""
from __future__ import annotations

import datetime
import math

from app.models.scenario import SeaLevelRise
from app.simulations.engine import calculate_state

TICKS_PER_HORIZON = 240
DEFAULT_SPEED = 4.0
MIN_SPEED = 1.0
MAX_SPEED = 20.0


def build_live_state(
    *,
    restoration_level: float,
    sea_level_rise: SeaLevelRise,
    horizon_year: int,
    baseline_area_ha: float,
    baseline_carbon_density: float,
    params: dict[str, float],
    tick: int,
    virtual_start: datetime.datetime,
) -> dict:
    """Build a deterministic but changing observation for one stream tick."""
    progress = min(1.0, tick / TICKS_PER_HORIZON)
    model_state = calculate_state(
        restoration_level=restoration_level,
        sea_level_rise=sea_level_rise,
        progress=progress,
        baseline_area_ha=baseline_area_ha,
        baseline_carbon_density=baseline_carbon_density,
        params=params,
    )

    # A bounded seasonal signal makes the live chart visibly dynamic while
    # remaining reproducible and independent of random number generators.
    phase = tick / 12.0
    seasonal = math.sin(phase)
    cover = max(0.0, min(1.0, model_state["vegetation_cover"] + 0.025 * seasonal))
    water_table = -0.10 - 0.06 * seasonal - 0.02 * progress
    density = model_state["retained_carbon"] / max(model_state["effective_area_ha"], 0.01)
    soil_carbon = density * (0.84 + 0.01 * seasonal)
    biomass = density - soil_carbon
    retained = model_state["effective_area_ha"] * (soil_carbon + biomass)
    baseline_carbon = baseline_area_ha * baseline_carbon_density
    variation_pct = ((retained - baseline_carbon) / baseline_carbon * 100.0) if baseline_carbon else 0.0
    horizon_span_days = max(1, horizon_year - int(params.get("start_year", 2025))) * 365
    virtual_time = virtual_start + datetime.timedelta(days=horizon_span_days * progress)

    return {
        "type": "state",
        "sequence": tick,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "virtual_time": virtual_time.isoformat(),
        "source": "simulated",
        "values": {
            "water_table": round(water_table, 3),
            "vegetation_cover": round(cover, 4),
            "soil_organic_carbon": round(soil_carbon, 2),
            "biomass": round(biomass, 2),
            "retained_carbon": round(retained, 2),
            "effective_area_ha": model_state["effective_area_ha"],
            "variation_pct": round(variation_pct, 2),
        },
    }
