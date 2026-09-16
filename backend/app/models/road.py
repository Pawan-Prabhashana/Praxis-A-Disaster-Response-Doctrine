"""Road network segments and scenario-scoped closures."""

from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class RoadSegment(Base, PrimaryKeyMixin, TimestampMixin):
    """A road segment from OpenStreetMap."""

    __tablename__ = "road_segment"

    osm_id: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    road_class: Mapped[str | None] = mapped_column(String(40), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )

    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False), nullable=False
    )


class RoadClosure(Base, PrimaryKeyMixin, TimestampMixin):
    """A closure of a road segment within a scenario.

    Closures are scenario-scoped so the same road can be open in one event and
    closed in another. Real-time closure feeds for Sri Lanka are not openly
    available, so demo closures are generated and flagged ``is_synthetic``.
    """

    __tablename__ = "road_closure"
    __table_args__ = (
        UniqueConstraint("road_segment_id", "scenario_id", name="uq_road_closure_segment_scenario"),
    )

    road_segment_id: Mapped[int] = mapped_column(
        ForeignKey("road_segment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )
