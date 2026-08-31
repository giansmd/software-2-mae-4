"""Scenario CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user, require_role
from app.models.scenario import Scenario
from app.models.user import Role, User
from app.schemas.scenario import ScenarioCreate, ScenarioOut, ScenarioUpdate

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _authorize_owner_or_admin(user: User, scenario: Scenario) -> None:
    if user.role != Role.ADMIN and scenario.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso sobre este escenario")


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[Scenario]:
    q = db.query(Scenario)
    if user is None:
        return q.filter(Scenario.is_public.is_(True)).order_by(Scenario.id).all()
    if user.role == Role.ADMIN:
        return q.order_by(Scenario.id).all()
    return (
        q.filter((Scenario.owner_id == user.id) | (Scenario.is_public.is_(True)))
        .order_by(Scenario.id)
        .all()
    )


@router.post("", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INVESTIGADOR, Role.ADMIN)),
) -> Scenario:
    scenario = Scenario(**payload.model_dump(), owner_id=user.id)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Escenario no encontrado")
    if not scenario.is_public:
        if user is None or (user.role != Role.ADMIN and scenario.owner_id != user.id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso para ver este escenario")
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Escenario no encontrado")
    _authorize_owner_or_admin(user, scenario)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scenario, field, value)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Escenario no encontrado")
    _authorize_owner_or_admin(user, scenario)
    db.delete(scenario)
    db.commit()
