"""Hierarchical administrative regions (COD-AB)."""

from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class AdminRegion(Base, PrimaryKeyMixin, TimestampMixin):
    """A single administrative unit at some level of the COD-AB hierarchy.

    Levels: 0 country → 1 province → 2 district → 3 DS division → 4 GN division.
    Regions are linked by ``pcode``/``parent_pcode`` (P-codes are the stable
    HDX identifiers) so the tree can be rebuilt without surrogate-id coupling.
    """

    __tablename__ = "admin_region"
    # A table-level unique constraint (rather than a unique index) so the
    # self-referential parent_pcode FK can reference pcode.
    __table_args__ = (UniqueConstraint("pcode", name="uq_admin_region_pcode"),)

    level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pcode: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_pcode: Mapped[str | None] = mapped_column(
        ForeignKey("admin_region.pcode", ondelete="SET NULL"), nullable=True, index=True
    )
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_si: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_ta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )

    # MultiPolygon in WGS84. GIST index is created explicitly in the migration.
    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )
