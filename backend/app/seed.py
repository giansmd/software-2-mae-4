"""Database seeding: demo users, calibration params, public demo scenarios and samples.

Idempotent: safe to run on every backend startup. Creates the schema if missing
and only inserts rows that are not already present.
"""
from __future__ import annotations

import datetime

from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.measurement import Measurement
from app.models.model_param import ModelParam
from app.models.scenario import Scenario, SeaLevelRise
from app.models.user import Role, User
from app.services.security import hash_password
from app.simulations.engine import DEFAULT_PARAMS


PARAM_META: dict[str, tuple[str | None, str]] = {
    "start_year": ("año", "Año inicial de la proyección (línea base)."),
    "restoration_boost_max": (
        "fracción",
        "Ganancia máxima de densidad de carbono a restauración hidrológica total (curva saturante).",
    ),
    "restoration_k": ("1/fracción", "Pendiente (k) de la curva saturante de restauración."),
    "slr_area_loss_low": ("fracción", "Fracción de área del humedal perdida al horizonte — SLR IPCC bajo."),
    "slr_area_loss_medium": ("fracción", "Fracción de área perdida al horizonte — SLR IPCC medio."),
    "slr_area_loss_high": ("fracción", "Fracción de área perdida al horizonte — SLR IPCC alto."),
    "slr_density_loss_low": ("fracción", "Reducción de densidad de carbono al horizonte — SLR IPCC bajo."),
    "slr_density_loss_medium": ("fracción", "Reducción de densidad de carbono al horizonte — SLR IPCC medio."),
    "slr_density_loss_high": ("fracción", "Reducción de densidad de carbono al horizonte — SLR IPCC alto."),
}


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ---- Users (one per role) ----
        def ensure_user(email: str, password: str, full_name: str, role: Role, institution: str) -> User:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                return existing
            user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                institution=institution,
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        ensure_user("admin@mae4.dev", "Admin12345", "Administrador MAE-4", Role.ADMIN, "Universidad Nacional")
        inv = ensure_user("inv@mae4.dev", "Invest12345", "Investigador MAE-4", Role.INVESTIGADOR, "Universidad Nacional")
        ensure_user("visit@mae4.dev", "Visit12345", "Visitante Demo", Role.VISITANTE, "Público")

        # ---- Calibration parameters ----
        for key, value in DEFAULT_PARAMS.items():
            if db.query(ModelParam).filter(ModelParam.key == key).first():
                continue
            unit, description = PARAM_META.get(key, (None, None))
            db.add(ModelParam(key=key, value=value, unit=unit, description=description))
        db.commit()

        # ---- Public demo scenarios ----
        if not db.query(Scenario).filter(Scenario.is_public.is_(True)).first():
            demos = [
                Scenario(
                    name="Línea base (sin restauración)",
                    description="Humedal costero sin intervención; solo efecto del aumento del nivel del mar (IPCC medio).",
                    restoration_level=0.0,
                    sea_level_rise=SeaLevelRise.MEDIUM,
                    horizon_year=2050,
                    is_public=True,
                    owner_id=None,
                ),
                Scenario(
                    name="Restauración media + SLR medio",
                    description="Restauración hidrológica al 50% bajo proyección IPCC media.",
                    restoration_level=50.0,
                    sea_level_rise=SeaLevelRise.MEDIUM,
                    horizon_year=2050,
                    is_public=True,
                    owner_id=None,
                ),
                Scenario(
                    name="Restauración alta + SLR bajo",
                    description="Restauración al 90% bajo proyección IPCC baja; caso que valida la hipótesis.",
                    restoration_level=90.0,
                    sea_level_rise=SeaLevelRise.LOW,
                    horizon_year=2050,
                    is_public=True,
                    owner_id=None,
                ),
                Scenario(
                    name="Restauración alta + SLR alto",
                    description="Restauración al 90% pero con subida del nivel del mar IPCC alta (estrés máximo).",
                    restoration_level=90.0,
                    sea_level_rise=SeaLevelRise.HIGH,
                    horizon_year=2050,
                    is_public=True,
                    owner_id=None,
                ),
            ]
            for s in demos:
                db.add(s)
            db.commit()

        # ---- Demo measurements (temporal field data of the baseline wetland) ----
        if db.query(Measurement).count() == 0:
            baseline = db.query(Scenario).filter(Scenario.name == "Línea base (sin restauración)").first()
            if baseline:
                for i, year in enumerate(range(2020, 2026)):
                    db.add(
                        Measurement(
                            scenario_id=baseline.id,
                            owner_id=inv.id,
                            date=datetime.date(year, 1, 15),
                            vegetation_cover=round(0.50 + 0.02 * i, 3),
                            water_table=-0.10,
                            soil_organic_carbon=round(80.0 + 1.5 * i, 2),
                            biomass=round(10.0 + 0.6 * i, 2),
                            note="Dato de demostración del humedal costero tipo.",
                        )
                    )
                db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
    print("Seed completado.")
