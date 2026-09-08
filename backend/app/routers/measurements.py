"""Measurement / sample CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.measurement import Measurement
from app.models.scenario import Scenario
from app.models.user import Role, User
from app.schemas.measurement import MeasurementCreate, MeasurementOut, MeasurementUpdate

router = APIRouter(prefix="/measurements", tags=["measurements"])


def _authorize_owner_or_admin(user: User, measurement: Measurement) -> None:
    if user.role != Role.ADMIN and measurement.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso sobre esta medición")


def _ensure_scenario_accessible(scenario_id: int, user: User, db: Session) -> None:
    """Fail unless the scenario exists and the user may attach measurements to it."""
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Escenario no encontrado")
    if user.role != Role.ADMIN and not scenario.is_public and scenario.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso sobre este escenario")


@router.get("", response_model=list[MeasurementOut])
def list_measurements(
    scenario_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> list[Measurement]:
    q = db.query(Measurement)
    if user.role != Role.ADMIN:
        q = q.filter(Measurement.owner_id == user.id)
    if scenario_id is not None:
        q = q.filter(Measurement.scenario_id == scenario_id)
    return q.order_by(Measurement.date.desc()).all()


@router.post("", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
def create_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> Measurement:
    if payload.scenario_id is not None:
        _ensure_scenario_accessible(payload.scenario_id, user, db)
    measurement = Measurement(**payload.model_dump(), owner_id=user.id)
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get("/{measurement_id}", response_model=MeasurementOut)
def get_measurement(
    measurement_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Measurement:
    measurement = db.get(Measurement, measurement_id)
    if measurement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medición no encontrada")
    _authorize_owner_or_admin(user, measurement)
    return measurement


@router.put("/{measurement_id}", response_model=MeasurementOut)
def update_measurement(
    measurement_id: int,
    payload: MeasurementUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Measurement:
    measurement = db.get(Measurement, measurement_id)
    if measurement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medición no encontrada")
    _authorize_owner_or_admin(user, measurement)
    if payload.scenario_id is not None and payload.scenario_id != measurement.scenario_id:
        _ensure_scenario_accessible(payload.scenario_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(measurement, field, value)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    measurement_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    measurement = db.get(Measurement, measurement_id)
    if measurement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medición no encontrada")
    _authorize_owner_or_admin(user, measurement)
    db.delete(measurement)
    db.commit()