"""Model calibration parameter endpoints (read for all auth users, write ADMIN)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.model_param import ModelParam
from app.models.user import Role, User
from app.schemas.model_param import ModelParamOut, ModelParamUpdate

router = APIRouter(prefix="/model-params", tags=["model-params"])


@router.get("", response_model=list[ModelParamOut])
def list_params(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ModelParam]:
    return db.query(ModelParam).order_by(ModelParam.key).all()


@router.put("/{key}", response_model=ModelParamOut)
def update_param(
    key: str,
    payload: ModelParamUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
) -> ModelParam:
    param = db.query(ModelParam).filter(ModelParam.key == key).first()
    if param is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parámetro no encontrado")
    param.value = payload.value
    db.commit()
    db.refresh(param)
    return param
