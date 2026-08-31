"""Measurement / sample CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.measurement import Measurement
from app.models.user import Role, User
from app.schemas.measurement import MeasurementCreate, MeasurementOut, MeasurementUpdate

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("", response_model=list[MeasurementOut])
def list_measurements(
    scenario_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> list[Measurement]:
    q = db.query(Measurement)
    if scenario_id is not None:
        q = q.filter(Measurement.scenario_id == scenario_id)
    return q.order_by(Measurement.date.desc()).all()


@router.post("", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
def create_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> Measurement:
    measurement = Measurement(**payload.model_dump(), owner_id=user.id)
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get("/{measurement_id}", response_model=MeasurementOut)
def get_measurement(
    measurement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Measurement:
    measurement = db.get(Measurement, measurement_id)
    if measurement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medición no encontrada")
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
    if user.role != Role.ADMIN and measurement.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso sobre esta medición")
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
    if user.role != Role.ADMIN and measurement.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso sobre esta medición")
    db.delete(measurement)
    db.commit()
