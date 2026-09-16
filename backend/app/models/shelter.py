"""Candidate shelters (derived from OSM facilities — NOT an official registry)."""

from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Shelter(Base, PrimaryKeyMixin, TimestampMixin):
    """A CANDIDATE shelter location.

    Open, authoritative shelter registries are scarce, so these are derived from
    OpenStreetMap facilities (schools, community centres) and are explicitly
    candidates — not an official DMC shelter list. ``capacity`` is only set when
    a synthetic estimate is generated, in which case ``is_synthetic`` is true.
    """

    __tablename__ = "shelter"

    osm_id: Mapped[str | None] = mapped_column(String(40), nullable=True, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(60), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    admin_region_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_region.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
