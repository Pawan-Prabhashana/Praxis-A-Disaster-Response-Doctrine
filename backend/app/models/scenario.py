"""Scenario — a disaster event (historical, simulated, or live)."""

from __future__ import annotations

from datetime import date

from geoalchemy2 import Geometry
from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import HazardType, ScenarioStatus
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Scenario(Base, PrimaryKeyMixin, TimestampMixin):
    """A disaster event that ties together hazard layers, incidents, and assets.

    The seeded real event is one row. ``bbox_*`` is the geographic extent (for
    map fit-bounds); ``center`` is a representative point.
    """

    __tablename__ = "scenario"

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hazard_type: Mapped[HazardType] = mapped_column(
        SAEnum(
            HazardType,
            native_enum=False,
            length=20,
            name="hazard_type",
            values_callable=lambda enum: [e.value for e in enum],
            create_constraint=True,
        ),
        nullable=False,
    )
    status: Mapped[ScenarioStatus] = mapped_column(
        SAEnum(
            ScenarioStatus,
            native_enum=False,
            length=20,
            name="scenario_status",
            values_callable=lambda enum: [e.value for e in enum],
            create_constraint=True,
        ),
        nullable=False,
    )
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    bbox_min_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_min_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_max_lat: Mapped[float | None] = mapped_column(Float, nullable=True)

    center: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )
