"""Schemas for playbooks (response strategies) and their levers."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.services.scoring.models import LEVER_SCHEMA_VERSION, ScoreResult


class EvacuationPolicy(BaseModel):
    """When a region should evacuate, in explainable real terms."""

    # Regions whose at-risk population is at least this are flagged for evacuation.
    at_risk_threshold: int = Field(default=0, ge=0)


class ResourcePosture(BaseModel):
    """User-entered planning decision variables (not real-data)."""

    response_teams: int = Field(default=0, ge=0, le=100000)
    boats: int = Field(default=0, ge=0, le=100000)
    allocation: Literal["proportional_to_need", "even"] = "proportional_to_need"


class AccessPolicy(BaseModel):
    """How the strategy treats road access (closures are synthetic)."""

    avoid_closed_roads: bool = True


class LeverSet(BaseModel):
    """The complete, versioned set of decisions that defines a playbook."""

    version: int = LEVER_SCHEMA_VERSION
    priority_region_pcodes: list[str] = Field(default_factory=list)
    activated_shelter_ids: list[int] = Field(default_factory=list)
    evacuation: EvacuationPolicy = Field(default_factory=EvacuationPolicy)
    resources: ResourcePosture = Field(default_factory=ResourcePosture)
    access: AccessPolicy = Field(default_factory=AccessPolicy)


class RegionContext(BaseModel):
    """A candidate priority region with its real population + at-risk estimate."""

    pcode: str
    name: str
    population: int
    at_risk_population: float
    is_access_impaired: bool


class SheltersInRegions(BaseModel):
    """Candidate shelter ids within a set of regions (for shelter activation)."""

    ids: list[int]
    total: int


class PlaybookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    levers: LeverSet = Field(default_factory=LeverSet)


class PlaybookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    levers: LeverSet | None = None


class PlaybookRead(BaseModel):
    id: int
    scenario_slug: str
    name: str
    description: str | None
    levers: LeverSet
    score_result: ScoreResult | None
    created_at: datetime
    updated_at: datetime
