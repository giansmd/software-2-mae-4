"""Model calibration parameter endpoints (read for all auth users, write ADMIN)."""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.model_param import ModelParam
from app.models.user import Role, User
from app.schemas.model_param import ModelParamOut, ModelParamUpdate

router = APIRouter(prefix="/model-params", tags=["model-params"])

# Valid ranges per calibration key (VALID-001). Fractions are bounded to 0..1
# (restoration gain and SLR losses are proportions of the baseline), the
# restoration curve slope must be non-negative, and the baseline year is kept
# in a plausible window. Non-finite values (inf/NaN) are rejected outright so
# the engine never consumes invalid scientific inputs.
PARAM_RANGES: dict[str, tuple[float, float]] = {
    "start_year": (1900.0, 2100.0),
    "restoration_boost_max": (0.0, 1.0),
    "restoration_k": (0.0, 50.0),
    "slr_area_loss_low": (0.0, 1.0),
    "slr_area_loss_medium": (0.0, 1.0),
    "slr_area_loss_high": (0.0, 1.0),
    "slr_density_loss_low": (0.0, 1.0),
    "slr_density_loss_medium": (0.0, 1.0),
    "slr_density_loss_high": (0.0, 1.0),
}


def validate_param_value(key: str, value: float) -> None:
    """Reject non-finite or out-of-range calibration values with HTTP 422."""
    if not math.isfinite(value):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"El valor de '{key}' debe ser finito",
        )
    bounds = PARAM_RANGES.get(key)
    if bounds is not None:
        low, high = bounds
        if not (low <= value <= high):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                f"El valor de '{key}' debe estar entre {low:g} y {high:g}",
            )


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
    validate_param_value(key, payload.value)
    param.value = payload.value
    db.commit()
    db.refresh(param)
    return param
