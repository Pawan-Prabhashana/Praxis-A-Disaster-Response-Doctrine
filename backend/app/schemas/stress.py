"""Request/response schemas for stress-test endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.services.scoring.stress import StressResult
from app.services.scoring.uncertainty import UncertaintyConfig


class StressTestRequest(BaseModel):
    """Parameters for a stress-test run.

    ``config`` overrides the default UncertaintyConfig (the UI sends the full,
    toggled config back). ``seed`` is optional; when omitted the server generates
    and records one so the run stays reproducible.
    """

    config: UncertaintyConfig | None = None
    n_iterations: int = Field(default=500, ge=50, le=5000)
    seed: int | None = Field(default=None, ge=0, le=2_147_483_647)


class StressRunRead(BaseModel):
    """A persisted stress-test run with its aggregated result."""

    id: int
    playbook_id: int
    scenario_slug: str
    n_iterations: int
    seed: int
    created_at: datetime
    result: StressResult
