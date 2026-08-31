"""Import all models so they register on Base.metadata when imported."""
from app.models.user import Role, User
from app.models.scenario import SeaLevelRise, Scenario
from app.models.measurement import Measurement
from app.models.model_param import ModelParam

__all__ = [
    "Role",
    "User",
    "SeaLevelRise",
    "Scenario",
    "Measurement",
    "ModelParam",
]
