"""Load calibration parameters from the database into a plain dict."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.model_param import ModelParam


def load_model_params(db: Session) -> dict[str, float]:
    rows = db.query(ModelParam).all()
    return {r.key: float(r.value) for r in rows}
