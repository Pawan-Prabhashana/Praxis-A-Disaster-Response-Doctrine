"""The trust boundary: assemble ONLY real computed facts into ``BriefFacts``.

Everything a brief may state as fact lives here, already computed by the
Phase-4 scoring core and the Phase-5 stress engine. The generator (LLM or
template) receives ``BriefFacts`` and nothing else; the numeric guard
(``guard.py``) verifies the generated prose against it. Assembling this object
is pure and deterministic — no DB, HTTP, clock, or randomness.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.playbook import LeverSet
from app.services.scoring.models import Provenance, ScoreResult, ScoringInputs
from app.services.scoring.stress import StressResult

BRIEF_FACTS_VERSION = 1

# Human labels for the scoring-core metric keys (kept here so both the template
# and the prompt share one vocabulary).
METRIC_LABELS: dict[str, str] = {
    "population_coverage": "Population coverage",
    "shelter_adequacy": "Shelter adequacy",
    "accessibility": "Accessibility",
    "resource_adequacy": "Resource adequacy",
}


class ScenarioFacts(BaseModel):
    """Real scenario identity (no derived judgement)."""

    slug: str
    name: str
    hazard_type: str
    status: str
    event_date: date | None
    description: str | None


class PriorityRegionFact(BaseModel):
    """A prioritised district in plain terms (real population + at-risk)."""

    pcode: str
    name: str
    population: int
    at_risk_population: int
    is_access_impaired: bool


class StrategyFacts(BaseModel):
    """The playbook's levers translated to plain, factual terms."""

    name: str
    description: str | None
    priority_regions: list[PriorityRegionFact]
    priority_region_count: int
    activated_shelter_count: int
    activated_capacity: int
    capacity_known: int
    capacity_assumed: int
    assumed_capacity_shelters: int
    response_teams: int
    boats: int
    team_capacity: int
    boat_capacity: int
    response_capacity: int
    allocation: str
    evacuation_threshold: int
    avoid_closed_roads: bool
    displacement_rate_pct: int


class MetricFact(BaseModel):
    """One scorecard dimension, display-ready, with its honesty class."""

    key: str
    label: str
    score: float  # 0..100, one decimal
    weight_pct: int  # weight as a whole percentage
    provenance: Provenance
    raw: dict[str, float | int | str]
    notes: list[str] = Field(default_factory=list)


class ScorecardFacts(BaseModel):
    """The deterministic scorecard (Phase 4)."""

    overall: float  # 0..100
    metrics: list[MetricFact]
    total_at_risk: int
    covered_at_risk: int
    uncovered_at_risk: int
    people_needing_shelter: int
    coverage_gap_count: int


class CoverageGapFact(BaseModel):
    pcode: str
    name: str
    at_risk_population: int


class RobustnessFacts(BaseModel):
    """Stress-test robustness (Phase 5) — modeled (epistemic) uncertainty."""

    point_overall: float
    median: float
    p05: float
    p25: float
    p75: float
    p95: float
    worst_plausible: float
    probability_meets_target_pct: int
    target_score: int
    n_iterations: int
    seed: int
    uses_synthetic_data: bool
    epistemic_note: str
    # True when the deterministic point score materially overstates the median.
    point_is_optimistic: bool


class BriefFacts(BaseModel):
    """The complete, real-fact input to the brief generator (trust boundary)."""

    version: int = BRIEF_FACTS_VERSION
    scenario: ScenarioFacts
    strategy: StrategyFacts
    scorecard: ScorecardFacts
    coverage_gaps: list[CoverageGapFact]
    robustness: RobustnessFacts | None
    assumptions: list[str]
    synthetic_influences: list[str]
    uses_synthetic_data: bool


def _int(value: float | int | str, default: int = 0) -> int:
    try:
        return round(float(value))
    except (TypeError, ValueError):
        return default


def build_brief_facts(
    scenario: ScenarioFacts,
    playbook_name: str,
    playbook_description: str | None,
    levers: LeverSet,
    inputs: ScoringInputs,
    score_result: ScoreResult,
    stress_result: StressResult | None,
) -> BriefFacts:
    """Assemble the typed, real-fact brief input from computed results only."""
    by_pcode = {r.pcode: r for r in inputs.regions}
    priority = [
        PriorityRegionFact(
            pcode=r.pcode,
            name=r.name,
            population=r.population,
            at_risk_population=round(r.at_risk_population),
            is_access_impaired=r.is_access_impaired,
        )
        for r in inputs.regions
        if r.is_priority
    ]
    priority.sort(key=lambda r: -r.at_risk_population)

    a = inputs.assumptions
    response_capacity = (
        inputs.resources.response_teams * a.team_capacity + inputs.resources.boats * a.boat_capacity
    )
    strategy = StrategyFacts(
        name=playbook_name,
        description=playbook_description,
        priority_regions=priority,
        priority_region_count=len(priority),
        activated_shelter_count=inputs.shelters.activated_count,
        activated_capacity=round(inputs.shelters.capacity_known + inputs.shelters.capacity_assumed),
        capacity_known=round(inputs.shelters.capacity_known),
        capacity_assumed=round(inputs.shelters.capacity_assumed),
        assumed_capacity_shelters=inputs.shelters.assumed_capacity_count,
        response_teams=inputs.resources.response_teams,
        boats=inputs.resources.boats,
        team_capacity=a.team_capacity,
        boat_capacity=a.boat_capacity,
        response_capacity=response_capacity,
        allocation=inputs.resources.allocation,
        evacuation_threshold=levers.evacuation.at_risk_threshold,
        avoid_closed_roads=levers.access.avoid_closed_roads,
        displacement_rate_pct=round(a.displacement_rate * 100),
    )

    metrics = [
        MetricFact(
            key=m.key,
            label=METRIC_LABELS.get(m.key, m.key),
            score=round(m.score * 100, 1),
            weight_pct=round(m.weight * 100),
            provenance=m.provenance,
            raw=m.raw,
            notes=m.notes,
        )
        for m in score_result.metrics
    ]
    gaps = [
        CoverageGapFact(
            pcode=g.pcode,
            name=by_pcode[g.pcode].name if g.pcode in by_pcode else g.name,
            at_risk_population=round(g.at_risk_population),
        )
        for g in score_result.coverage_gaps
    ]

    scorecard = ScorecardFacts(
        overall=score_result.overall,
        metrics=metrics,
        total_at_risk=_int(score_result.totals.get("total_at_risk", 0)),
        covered_at_risk=_int(score_result.totals.get("covered_at_risk", 0)),
        uncovered_at_risk=_int(score_result.totals.get("uncovered_at_risk", 0)),
        people_needing_shelter=_int(score_result.totals.get("people_needing_shelter", 0)),
        coverage_gap_count=len(gaps),
    )

    robustness: RobustnessFacts | None = None
    if stress_result is not None:
        r = stress_result.robustness
        robustness = RobustnessFacts(
            point_overall=stress_result.point_overall,
            median=r.median,
            p05=stress_result.overall.p05,
            p25=stress_result.overall.p25,
            p75=stress_result.overall.p75,
            p95=stress_result.overall.p95,
            worst_plausible=r.worst_plausible,
            probability_meets_target_pct=round(r.probability_meets_target * 100),
            target_score=round(r.target_score),
            n_iterations=stress_result.n_iterations,
            seed=stress_result.seed,
            uses_synthetic_data=stress_result.uses_synthetic_data,
            epistemic_note=stress_result.epistemic_note,
            point_is_optimistic=(stress_result.point_overall - r.median) >= 3.0,
        )

    synthetic_influences = _synthetic_influences(metrics)

    return BriefFacts(
        scenario=scenario,
        strategy=strategy,
        scorecard=scorecard,
        coverage_gaps=gaps,
        robustness=robustness,
        assumptions=list(score_result.assumptions_used),
        synthetic_influences=synthetic_influences,
        uses_synthetic_data=score_result.uses_synthetic_data,
    )


def _synthetic_influences(metrics: list[MetricFact]) -> list[str]:
    """Name the metrics whose value rests on synthetic sample data."""
    out: list[str] = []
    for m in metrics:
        if m.provenance is Provenance.SYNTHETIC:
            out.append(
                f"{m.label} is computed from synthetic road-closure sample data "
                "(indicative only, not an official record)."
            )
    return out
