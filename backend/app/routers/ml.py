"""ML endpoints: surrogate-model metadata and predictions.

The prediction is returned side by side with the deterministic engine output so
callers can see how closely the learned emulator matches the scientific model.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_optional_user
from app.ml import registry
from app.models.scenario import Scenario
from app.models.user import Role, User
from app.schemas.ml import MLMetadata, MLPredictionRequest, MLPredictionResult
from app.services.params import load_model_params
from app.simulations.engine import InvalidSimulationParamsError, run_simulation

router = APIRouter(prefix="/ml", tags=["ml"])


def _ensure_enabled() -> None:
    if not settings.ml_enabled:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El modelo de IA está deshabilitado (ML_ENABLED=false)",
        )


def _run_checked(**kwargs) -> dict:
    try:
        return run_simulation(**kwargs)
    except InvalidSimulationParamsError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


def _resolve_engine(db: Session, payload: MLPredictionRequest, user: User | None) -> dict:
    params = load_model_params(db)
    if payload.scenario_id is not None:
        scenario = db.get(Scenario, payload.scenario_id)
        if scenario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Escenario no encontrado")
        if not scenario.is_public:
            if user is None or (user.role != Role.ADMIN and scenario.owner_id != user.id):
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "No tiene permiso para predecir este escenario",
                )
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


def _build_result(engine: dict) -> MLPredictionResult:
    ml = registry.predict(
        restoration_level=engine["restoration_level"],
        sea_level_rise=engine["sea_level_rise"],
        horizon_year=engine["horizon_year"],
        baseline_area_ha=engine["baseline_area_ha"],
        baseline_carbon_density=engine["baseline_carbon_density"],
    )
    return MLPredictionResult(
        scenario_id=engine.get("scenario_id"),
        scenario_name=engine["scenario_name"],
        restoration_level=engine["restoration_level"],
        sea_level_rise=engine["sea_level_rise"],
        horizon_year=engine["horizon_year"],
        baseline_area_ha=engine["baseline_area_ha"],
        baseline_carbon_density=engine["baseline_carbon_density"],
        ml_variation_pct=ml["variation_pct"],
        ml_horizon_carbon=ml["horizon_carbon"],
        ml_meets_hypothesis=ml["meets_hypothesis"],
        ml_meets_hypothesis_probability=ml["meets_hypothesis_probability"],
        engine_variation_pct=engine["horizon_variation_pct"],
        engine_horizon_carbon=engine["horizon_carbon"],
        engine_meets_hypothesis=engine["meets_hypothesis"],
        delta_variation_pct=round(ml["variation_pct"] - engine["horizon_variation_pct"], 2),
        hypothesis_threshold_pct=engine["hypothesis_threshold_pct"],
    )


@router.get("/metadata", response_model=MLMetadata)
def metadata() -> MLMetadata:
    _ensure_enabled()
    return MLMetadata(**registry.get_metadata())


@router.post("/predict", response_model=MLPredictionResult)
def predict(
    payload: MLPredictionRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> MLPredictionResult:
    _ensure_enabled()
    return _build_result(_resolve_engine(db, payload, user))


@router.get("/predict/{scenario_id}", response_model=MLPredictionResult)
def predict_for_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> MLPredictionResult:
    _ensure_enabled()
    return _build_result(
        _resolve_engine(db, MLPredictionRequest(scenario_id=scenario_id), user)
    )
