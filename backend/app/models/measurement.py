"""Measurement / sample model: temporal field data of the wetland."""
from __future__ import annotations

import datetime

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id"), nullable=True, index=True
    )
    # Optional link to the uploading user
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    date: Mapped[datetime.date] = mapped_column(Date, index=True)

    # Vegetation cover fraction (0-1) or percentage
    vegetation_cover: Mapped[float] = mapped_column(Float)
    # Water table depth (m, negative = above surface)
    water_table: Mapped[float] = mapped_column(Float)
    # Soil organic carbon (tC/ha)
    soil_organic_carbon: Mapped[float] = mapped_column(Float)
    # Above-ground biomass (t/ha)
    biomass: Mapped[float] = mapped_column(Float)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)
