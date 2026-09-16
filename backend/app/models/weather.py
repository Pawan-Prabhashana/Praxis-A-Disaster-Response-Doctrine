"""Weather readings (Open-Meteo forecast/history)."""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class WeatherReading(Base, PrimaryKeyMixin, TimestampMixin):
    """A weather observation/forecast at a point (optionally tied to a region)."""

    __tablename__ = "weather_reading"
    __table_args__ = (
        UniqueConstraint("location_key", "valid_time", name="uq_weather_location_time"),
    )

    # Stable key for the sampling location (e.g. "kalu-ratnapura").
    location_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    valid_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    admin_region_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_region.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )

    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
