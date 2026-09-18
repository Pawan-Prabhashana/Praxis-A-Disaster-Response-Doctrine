"""After-action review — a persisted, auditable predicted-vs-recorded analysis."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class AfterAction(Base, PrimaryKeyMixin, TimestampMixin):
    """A predicted-vs-recorded after-action review for a playbook.

    Stores the pure analysis snapshot (``result``) and the lessons + narrated
    assessment (``lessons``) so the review is reproducible and auditable.
    """

    __tablename__ = "after_action"

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    playbook_id: Mapped[int] = mapped_column(
        ForeignKey("playbook.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brief_id: Mapped[int | None] = mapped_column(
        ForeignKey("brief.id", ondelete="SET NULL"), nullable=True
    )
    stress_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("stress_run.id", ondelete="SET NULL"), nullable=True
    )
    event_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generator: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    lessons: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
