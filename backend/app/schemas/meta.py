"""Schemas for the application metadata endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScenarioSummary(BaseModel):
    """Lightweight descriptor for a saved operational scenario.

    Populated in a later phase; the shape is fixed now so the frontend
    scenario-selector can be built against a stable contract.
    """

    id: str = Field(description="Stable scenario identifier.")
    name: str = Field(description="Human-readable scenario name.")


class MetaResponse(BaseModel):
    """Application metadata consumed by the frontend shell on boot."""

    app_name: str = Field(description="Product name.")
    version: str = Field(description="Running application version.")
    environment: str = Field(description="Deployment environment name.")
    scenarios: list[ScenarioSummary] = Field(
        default_factory=list,
        description="Available scenarios (empty until Phase 2 seeds them).",
    )
