"""Hazard layers — flood extents, landslide susceptibility, etc."""

from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LayerType
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class HazardLayer(Base, PrimaryKeyMixin, TimestampMixin):
    """A hazard geometry belonging to a scenario, or a standalone reference layer.

    ``scenario_id`` is nullable so standalone reference hazards (e.g. NBRO
    landslide susceptibility zonation) can exist independent of any one event.
    ``severity_class``/``severity_label`` carry the source's class attribute.
    """

    __tablename__ = "hazard_layer"

    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=True, index=True
    )
    layer_type: Mapped[LayerType] = mapped_column(
        SAEnum(
            LayerType,
            native_enum=False,
            length=32,
            name="layer_type",
            values_callable=lambda enum: [e.value for e in enum],
            create_constraint=True,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_source.id", ondelete="RESTRICT"), nullable=False
    )

    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    )
