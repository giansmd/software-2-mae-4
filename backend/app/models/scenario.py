"""Scenario model: a restoration + sea-level-rise simulation scenario."""
from __future__ import annotations

import datetime
import enum

from sqlalchemy import Boolean, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SeaLevelRise(str, enum.Enum):
    LOW = "low"  # IPCC bajo (≈ +0.4 m para 2100)
    MEDIUM = "medium"  # IPCC medio (≈ +0.7 m)
    HIGH = "high"  # IPCC alto (≈ +1.0 m)


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # owner is nullable for public demo scenarios seeded by the system
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # Restoration intervention level (0-100 %)
    restoration_level: Mapped[float] = mapped_column(Float, default=0.0)

    # Sea level rise projection (IPCC)
    sea_level_rise: Mapped[SeaLevelRise] = mapped_column(
        SAEnum(SeaLevelRise), default=SeaLevelRise.MEDIUM
    )

    # Horizon year for the projection (e.g. 2050)
    horizon_year: Mapped[int] = mapped_column(Integer, default=2050)

    # Baseline wetland characteristics (overridable per scenario)
    baseline_area_ha: Mapped[float] = mapped_column(Float, default=120.0)
    baseline_carbon_density: Mapped[float] = mapped_column(Float, default=85.0)

    # Public demo scenarios are readable without authentication
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(datetime.timezone.utc))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc)
    )
