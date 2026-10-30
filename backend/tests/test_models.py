"""Pruebas unitarias de los modelos de dominio.

Cubren enums, valores por defecto, restricciones de unicidad y relaciones
básicas sobre una base SQLite en memoria, sin tocar la base real.
"""
from __future__ import annotations

import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.measurement import Measurement
from app.models.model_param import ModelParam
from app.models.scenario import Scenario, SeaLevelRise
from app.models.user import Role, User


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)


def _user(session: Session, email: str = "a@example.org") -> User:
    user = User(
        email=email,
        hashed_password="x",
        full_name="Prueba",
        role=Role.INVESTIGADOR,
    )
    session.add(user)
    session.commit()
    return user


def test_roles_y_escenarios_marinos():
    assert [r.value for r in Role] == ["ADMIN", "INVESTIGADOR", "VISITANTE"]
    assert [s.value for s in SeaLevelRise] == ["low", "medium", "high"]


def test_scenario_defaults(session):
    scenario = Scenario(name="Base")
    session.add(scenario)
    session.commit()
    session.refresh(scenario)

    assert scenario.restoration_level == 0.0
    assert scenario.sea_level_rise is SeaLevelRise.MEDIUM
    assert scenario.horizon_year == 2050
    assert scenario.baseline_area_ha == 120.0
    assert scenario.baseline_carbon_density == 85.0
    assert scenario.is_public is False
    assert scenario.owner_id is None
    assert scenario.created_at is not None


def test_scenario_publico_sin_dueno(session):
    scenario = Scenario(name="Demo", is_public=True, restoration_level=90.0)
    session.add(scenario)
    session.commit()
    assert scenario.is_public is True
    assert scenario.owner_id is None


def test_usuario_email_unico(session):
    _user(session, "dup@example.org")
    with pytest.raises(IntegrityError):
        session.add(User(email="dup@example.org", hashed_password="y", full_name="Otro"))
        session.commit()
    session.rollback()


def test_usuario_defaults(session):
    user = _user(session)
    assert user.role is Role.INVESTIGADOR
    assert user.is_active is True
    assert user.token_version == 0
    assert user.institution is None


def test_measurement_requiere_campos(session):
    user = _user(session)
    measurement = Measurement(
        owner_id=user.id,
        date=datetime.date(2026, 10, 29),
        vegetation_cover=0.75,
        water_table=-0.2,
        soil_organic_carbon=95.0,
        biomass=180.0,
    )
    session.add(measurement)
    session.commit()
    session.refresh(measurement)

    assert measurement.id is not None
    assert measurement.scenario_id is None
    assert measurement.vegetation_cover == pytest.approx(0.75)


def test_model_param_clave_unica(session):
    session.add(ModelParam(key="restoration_k", value=2.5, unit="-"))
    session.commit()
    with pytest.raises(IntegrityError):
        session.add(ModelParam(key="restoration_k", value=3.0))
        session.commit()
    session.rollback()
