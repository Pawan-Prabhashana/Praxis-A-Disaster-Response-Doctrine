"""Brief — a persisted, auditable operational brief for a playbook.

Stores a SNAPSHOT of the facts it was built from (so the brief stays reproducible
and auditable even if the underlying data changes later), the generated content,
and the numeric-guard report + generation metadata.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, TimestampMixin


class Brief(Base, PrimaryKeyMixin, TimestampMixin):
    """A generated operational brief tied to a playbook (and optional stress run)."""

    __tablename__ = "brief"

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    playbook_id: Mapped[int] = mapped_column(
        ForeignKey("playbook.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stress_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("stress_run.id", ondelete="SET NULL"), nullable=True
    )
    # "llm" | "template" — how the narrative was produced.
    generator: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    guard: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
