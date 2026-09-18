"""Request/response schemas for the operational-brief endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.brief.content import BriefContent
from app.services.brief.facts import BriefFacts
from app.services.brief.guard import GuardReport


class BriefRequest(BaseModel):
    """Options for generating a brief.

    ``stress_run_id`` attaches a specific stress-test run's robustness to the
    brief; when omitted the playbook's most recent run (if any) is used.
    """

    stress_run_id: int | None = Field(default=None, ge=1)


class BriefRead(BaseModel):
    """A persisted brief: facts snapshot, generated content, and guard report."""

    id: int
    scenario_slug: str
    playbook_id: int
    stress_run_id: int | None
    generator: str
    model: str | None
    created_at: datetime
    facts: BriefFacts
    content: BriefContent
    guard: GuardReport


class BriefListItem(BaseModel):
    """Summary row for the brief history list."""

    id: int
    playbook_id: int
    stress_run_id: int | None
    generator: str
    model: str | None
    headline: str
    created_at: datetime
