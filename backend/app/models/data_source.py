"""Provenance for every ingested layer."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class DataSource(Base, PrimaryKeyMixin, TimestampMixin):
    """Where a piece of data came from.

    Every domain row references exactly one ``DataSource`` so the platform can
    always answer "where did this come from, and is it real?". Synthetic sample
    layers are marked ``is_synthetic=True`` here and on the rows themselves.
    """

    __tablename__ = "data_source"

    # Stable identifier used for idempotent upserts (e.g. "hdx-cod-ab-lka").
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
