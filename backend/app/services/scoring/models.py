"""Typed, serializable data structures for the scoring core.

These are plain data (pydantic) with no DB/HTTP coupling, so the scoring core is
unit-testable in isolation and Phase 5 can construct/perturb ``ScoringInputs``
directly. ``LEVER_SCHEMA_VERSION`` / ``SCORE_SCHEMA_VERSION`` keep the payloads
versioned for forward compatibility.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

LEVER_SCHEMA_VERSION = 1
SCORE_SCHEMA_VERSION = 1


class Provenance(StrEnum):
    """Where a metric's inputs come from — surfaced in the UI, never hidden."""

    REAL = "real"
    SYNTHETIC = "synthetic"  # derived from flagged sample data (e.g. road closures)
    ASSUMPTION = "assumption"  # derived from a documented planning assumption


class Assumptions(BaseModel):
    """Documented planning assumptions (constants, not real data)."""

    displacement_rate: float = 0.15  # fraction of at-risk population needing shelter
    team_capacity: int = 500  # people supportable per response team
    boat_capacity: int = 200  # people supportable per boat
    closed_road_buffer_m: int = 500  # shelter unreachable if within this of a closure
    assumed_shelter_capacity: dict[str, int] = Field(
        default_factory=lambda: {
            "school": 500,
            "college": 800,
            "community_centre": 200,
            "default": 300,
        }
    )


class RegionInput(BaseModel):
    """A district (admin level 2) with its real population and at-risk estimate."""

    pcode: str
    name: str
    population: int
    at_risk_population: float  # areal-weighted population inside the flood extent
    is_priority: bool
    is_access_impaired: bool  # a closed road intersects the region (synthetic input)


class ShelterInputs(BaseModel):
    """Aggregates over the activated (opened) shelters."""

    activated_count: int
    capacity_known: float  # summed real (OSM) capacity
    capacity_assumed: float  # summed assumed capacity for null-capacity shelters
    assumed_capacity_count: int  # how many activated shelters used an assumption
    reachable_activated_count: int  # not within buffer of a closed road (synthetic)


class ResourceInputs(BaseModel):
    """Resource posture — user-entered planning decision variables."""

    response_teams: int
    boats: int
    allocation: str  # "proportional_to_need" | "even"


class ScoringInputs(BaseModel):
    """Everything the pure core needs, already resolved from the database."""

    version: int = LEVER_SCHEMA_VERSION
    regions: list[RegionInput]
    shelters: ShelterInputs
    resources: ResourceInputs
    assumptions: Assumptions = Field(default_factory=Assumptions)
    uses_synthetic_closures: bool = True


class SubMetric(BaseModel):
    """One scored dimension with its raw numbers and provenance."""

    key: str
    score: float  # 0..1
    weight: float
    provenance: Provenance
    raw: dict[str, float | int | str]
    notes: list[str] = Field(default_factory=list)


class CoverageGap(BaseModel):
    """An at-risk region left out of the strategy's priority set."""

    pcode: str
    name: str
    at_risk_population: float


class ScoreResult(BaseModel):
    """The full, transparent scorecard for one playbook."""

    version: int = SCORE_SCHEMA_VERSION
    overall: float  # 0..100
    metrics: list[SubMetric]
    coverage_gaps: list[CoverageGap]
    totals: dict[str, float]
    uses_synthetic_data: bool
    assumptions_used: list[str]
