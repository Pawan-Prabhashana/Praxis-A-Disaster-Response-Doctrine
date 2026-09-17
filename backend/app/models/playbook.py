"""Playbook — a named, scenario-scoped response strategy."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Playbook(Base, PrimaryKeyMixin, TimestampMixin):
    """A response strategy for a scenario.

    ``levers`` is the versioned decision payload (see ``schemas.playbook.LeverSet``);
    ``score_result`` caches the last computed scorecard (see
    ``services.scoring.models.ScoreResult``). Both are JSONB so the schema can
    evolve without migrations while staying queryable.
    """

    __tablename__ = "playbook"

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    levers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    score_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
