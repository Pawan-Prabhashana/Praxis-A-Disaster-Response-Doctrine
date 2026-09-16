"""Incidents — point events (from DesInventar history or live reports)."""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Incident(Base, PrimaryKeyMixin, TimestampMixin):
    """A point-located event.

    ``type``/``severity`` are free strings because source vocabularies vary
    (DesInventar event types, field reports). ``external_id`` supports
    idempotent upserts per source.
    """

    __tablename__ = "incident"

    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(40), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    admin_region_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_region.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
