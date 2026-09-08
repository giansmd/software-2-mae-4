"""Simulation endpoints: run the carbon retention engine for a scenario or inline params."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_optional_user
from app.models.scenario import Scenario
from app.models.user import Role, User
from app.schemas.simulation import SimulationRequest, SimulationResult
from app.services.params import load_model_params
from app.simulations.engine import InvalidSimulationParamsError, run_simulation

router = APIRouter(prefix="/simulations", tags=["simulations"])


def _run_checked(**kwargs):
    """Ejecuta el motor traduciendo parámetros inconsistentes a HTTP 400 (ENG-001)."""
    try:
        return run_simulation(**kwargs)
    except InvalidSimulationParamsError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


def _resolve(db: Session, payload: SimulationRequest, user: User | None) -> dict:
    params = load_model_params(db)
    if payload.scenario_id is not None:
        scenario = db.get(Scenario, payload.scenario_id)
        if scenario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Escenario no encontrado")
        if not scenario.is_public:
            if user is None or (user.role != Role.ADMIN and scenario.owner_id != user.id):
                raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso para simular este escenario")
        return _run_checked(
            restoration_level=scenario.restoration_level,
            sea_level_rise=scenario.sea_level_rise,
            horizon_year=scenario.horizon_year,
            baseline_area_ha=scenario.baseline_area_ha,
            baseline_carbon_density=scenario.baseline_carbon_density,
            params=params,
            scenario_id=scenario.id,
            scenario_name=scenario.name,
        )
    required = [
        payload.restoration_level,
        payload.sea_level_rise,
        payload.horizon_year,
        payload.baseline_area_ha,
        payload.baseline_carbon_density,
    ]
    if any(v is None for v in required):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Debe proveer scenario_id o todos los parámetros inline "
            "(restoration_level, sea_level_rise, horizon_year, baseline_area_ha, baseline_carbon_density)",
        )
    return _run_checked(
        restoration_level=payload.restoration_level,
        sea_level_rise=payload.sea_level_rise,
        horizon_year=payload.horizon_year,
        baseline_area_ha=payload.baseline_area_ha,
        baseline_carbon_density=payload.baseline_carbon_density,
        params=params,
        scenario_name=payload.scenario_name or "Escenario personalizado",
    )


@router.post("/run", response_model=SimulationResult)
def run(payload: SimulationRequest, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)) -> SimulationResult:
    return SimulationResult(**_resolve(db, payload, user))


@router.get("/{scenario_id}", response_model=SimulationResult)
def run_for_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> SimulationResult:
    return SimulationResult(**_resolve(db, SimulationRequest(scenario_id=scenario_id), user))
