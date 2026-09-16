"""River points and their ensemble discharge forecasts (GloFAS via Open-Meteo).

The discharge ensemble spread is the uncertainty backbone consumed by Phase 5
(stress-testing response plans under hydrological uncertainty).
"""

from __future__ import annotations

from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class RiverPoint(Base, PrimaryKeyMixin, TimestampMixin):
    """A monitored river location for which discharge forecasts are fetched."""

    __tablename__ = "river_point"

    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    river_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )

    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )


class DischargeForecast(Base, PrimaryKeyMixin, TimestampMixin):
    """One day's ensemble river-discharge forecast for a river point (m³/s)."""

    __tablename__ = "discharge_forecast"
    __table_args__ = (
        UniqueConstraint(
            "river_point_id",
            "scenario_id",
            "valid_date",
            name="uq_discharge_point_scenario_date",
        ),
    )

    river_point_id: Mapped[int] = mapped_column(
        ForeignKey("river_point.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=True, index=True
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Ensemble statistics in m³/s.
    discharge_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    discharge_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    discharge_p25: Mapped[float | None] = mapped_column(Float, nullable=True)
    discharge_p75: Mapped[float | None] = mapped_column(Float, nullable=True)
    discharge_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    discharge_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )
