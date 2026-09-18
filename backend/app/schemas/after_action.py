"""Request/response schemas for the after-action (Learn) endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.after_action.lessons import LessonsContent
from app.services.after_action.models import AfterActionResult, DistrictOutcome


class AfterActionRequest(BaseModel):
    """Optional references to tie the review to a brief / stress run."""

    brief_id: int | None = Field(default=None, ge=1)
    stress_run_id: int | None = Field(default=None, ge=1)


class AfterActionRead(BaseModel):
    """A persisted after-action review."""

    id: int
    scenario_slug: str
    playbook_id: int
    brief_id: int | None
    stress_run_id: int | None
    event_year: int | None
    generator: str
    model: str | None
    created_at: datetime
    result: AfterActionResult
    lessons: LessonsContent


class AfterActionListItem(BaseModel):
    """Summary row for the after-action history."""

    id: int
    playbook_id: int
    event_year: int | None
    generator: str
    alignment_label: str
    created_at: datetime


class RecordedOutcomesResponse(BaseModel):
    """Aggregated REAL recorded impact per district (the actual historical baseline)."""

    scenario_slug: str
    event_year: int | None
    source: str = "DesInventar Sri Lanka — historical disaster loss database"
    is_synthetic: bool = False
    # Honest framing, carried in the payload so any consumer states it correctly.
    framing: str = (
        "Actual recorded impact of the historical event (DesInventar) — NOT the "
        "outcome of executing any Praxis playbook."
    )
    districts: list[DistrictOutcome]
    totals: dict[str, int]
