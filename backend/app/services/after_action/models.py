"""Typed, serializable structures for the after-action analysis.

Plain data (pydantic), no DB/HTTP coupling — so the analysis core is pure and
unit-testable, mirroring the Phase-4/5 scoring architecture.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

AFTER_ACTION_VERSION = 1

# Composite recorded-impact weights (documented in docs/AFTER_ACTION.md). Each
# component is min-max normalised across the district set first, so no raw scale
# dominates; loss of life is weighted highest, then homes destroyed, then people
# affected (exposure).
IMPACT_WEIGHTS: dict[str, float] = {
    "deaths": 0.5,
    "houses_destroyed": 0.3,
    "affected": 0.2,
}


class RegionPrediction(BaseModel):
    """The strategy's predicted view of a district (from Praxis scoring)."""

    pcode: str
    name: str
    at_risk_population: int
    is_priority: bool


class DistrictOutcome(BaseModel):
    """Real recorded impact for one district (aggregated DesInventar, one year).

    ``has_data`` is False when the district recorded no incidents in the window —
    surfaced as "no recorded data", never a fabricated zero-as-fact.
    """

    pcode: str
    name: str
    deaths: int = 0
    affected: int = 0
    houses_destroyed: int = 0
    incident_count: int = 0
    has_data: bool = False


class LessonSeverity(StrEnum):
    INFO = "info"
    WARN = "warn"
    CRIT = "crit"


class Lesson(BaseModel):
    """One structured, numbers-traceable lesson."""

    key: str
    severity: LessonSeverity
    title: str
    detail: str


class DistrictComparison(BaseModel):
    """Predicted vs. recorded for one district (the join, per district)."""

    pcode: str
    name: str
    # Predicted side (Praxis).
    at_risk_population: int
    is_priority: bool
    predicted_rank: int  # 1 = highest predicted at-risk
    # Recorded side (DesInventar, real).
    deaths: int
    affected: int
    houses_destroyed: int
    incident_count: int
    has_data: bool
    impact_score: float  # 0..100 composite (0 when no recorded data)
    impact_rank: int  # 1 = highest recorded impact
    # Predicted rank minus recorded rank: >0 = under-prioritised (recorded worse
    # than predicted), <0 = over-prioritised.
    rank_delta: int
    under_prioritised: bool  # high recorded impact, ranked lower than it deserved
    is_blind_spot: bool  # recorded impact but NOT in the priority set


class AlignmentMeasure(BaseModel):
    """How well predicted at-risk ranking matched recorded impact ranking."""

    spearman: float  # rank correlation in [-1, 1]
    label: str  # "strong" | "moderate" | "weak" | "inverted"
    top_k: int
    top_k_overlap: int  # districts in both predicted top-k and recorded top-k
    n_districts: int
    n_with_data: int


class AfterActionResult(BaseModel):
    """The full, pure after-action analysis (real numbers + flags, no narration)."""

    version: int = AFTER_ACTION_VERSION
    scenario_slug: str
    playbook_name: str
    event_year: int | None
    districts: list[DistrictComparison]
    alignment: AlignmentMeasure
    # Highest recorded impact first among districts NOT in the priority set.
    blind_spots: list[DistrictComparison] = Field(default_factory=list)
    # Highest recorded-impact district that was under-prioritised (the headline
    # lesson), if any.
    worst_under_prioritised: DistrictComparison | None = None
    totals: dict[str, int] = Field(default_factory=dict)
    impact_weights: dict[str, float] = Field(default_factory=lambda: dict(IMPACT_WEIGHTS))
    # Recorded outcomes are REAL DesInventar data; the predicted side uses Praxis
    # scoring which includes synthetic (road-closure) and assumption inputs.
    predicted_uses_synthetic: bool = True
    recorded_is_real: bool = True
