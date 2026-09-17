"""Stress-test run — a persisted Monte Carlo result for a playbook."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class StressRun(Base, PrimaryKeyMixin, TimestampMixin):
    """A reproducible stress-test of a playbook under modeled uncertainty.

    ``seed`` + ``config`` + the playbook's levers fully determine ``result``; we
    persist the aggregated summaries/histogram (JSONB), never the raw iterations.
    """

    __tablename__ = "stress_run"

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    playbook_id: Mapped[int] = mapped_column(
        ForeignKey("playbook.id", ondelete="CASCADE"), nullable=False, index=True
    )
    n_iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
