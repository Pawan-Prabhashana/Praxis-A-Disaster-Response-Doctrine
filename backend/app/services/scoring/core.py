"""The deterministic scoring core.

``score(inputs)`` is pure and referentially transparent: identical inputs always
yield an identical ``ScoreResult``. No randomness, DB, HTTP, or wall-clock. Every
metric maps to a formula documented in ``docs/SCORING.md``.

Phase 5 seam: to stress-test, build many perturbed ``ScoringInputs`` and call
``score`` over each — no change to this module is required.
"""

from __future__ import annotations

from app.services.scoring.models import (
    CoverageGap,
    Provenance,
    ScoreResult,
    ScoringInputs,
    SubMetric,
)

# Explicit, documented weighting (sums to 1.0). See docs/SCORING.md.
WEIGHTS: dict[str, float] = {
    "population_coverage": 0.35,
    "shelter_adequacy": 0.30,
    "accessibility": 0.15,
    "resource_adequacy": 0.20,
}


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Clamp numerator/denominator to [0, 1]; 0 when the denominator is 0."""
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def score(inputs: ScoringInputs) -> ScoreResult:
    """Compute the transparent scorecard for a resolved set of inputs."""
    a = inputs.assumptions
    priority = [r for r in inputs.regions if r.is_priority]

    total_at_risk = sum(r.at_risk_population for r in inputs.regions)
    covered_at_risk = sum(r.at_risk_population for r in priority)
    people_needing_shelter = a.displacement_rate * covered_at_risk

    metrics: list[SubMetric] = []

    # 1. Population coverage (real) — share of at-risk population prioritised.
    metrics.append(
        SubMetric(
            key="population_coverage",
            score=_safe_ratio(covered_at_risk, total_at_risk),
            weight=WEIGHTS["population_coverage"],
            provenance=Provenance.REAL,
            raw={
                "covered_at_risk": round(covered_at_risk),
                "total_at_risk": round(total_at_risk),
                "priority_regions": len(priority),
            },
        )
    )

    # 2. Shelter adequacy (real capacity + documented assumption for nulls).
    activated_capacity = inputs.shelters.capacity_known + inputs.shelters.capacity_assumed
    if people_needing_shelter <= 0:
        shelter_score = 1.0 if inputs.shelters.activated_count > 0 else 0.0
    else:
        shelter_score = _safe_ratio(activated_capacity, people_needing_shelter)
    shelter_notes: list[str] = []
    shelter_prov = Provenance.REAL
    if inputs.shelters.assumed_capacity_count > 0:
        shelter_prov = Provenance.ASSUMPTION
        shelter_notes.append(
            f"{inputs.shelters.assumed_capacity_count} activated shelter(s) used an "
            "assumed capacity (no capacity recorded in OSM)."
        )
    metrics.append(
        SubMetric(
            key="shelter_adequacy",
            score=shelter_score,
            weight=WEIGHTS["shelter_adequacy"],
            provenance=shelter_prov,
            raw={
                "activated_capacity": round(activated_capacity),
                "capacity_known": round(inputs.shelters.capacity_known),
                "capacity_assumed": round(inputs.shelters.capacity_assumed),
                "assumed_capacity_count": inputs.shelters.assumed_capacity_count,
                "people_needing_shelter": round(people_needing_shelter),
                "activated_shelters": inputs.shelters.activated_count,
            },
            notes=shelter_notes,
        )
    )

    # 3. Accessibility (SYNTHETIC — road closures are sample data).
    access_score = _safe_ratio(
        inputs.shelters.reachable_activated_count, inputs.shelters.activated_count
    )
    metrics.append(
        SubMetric(
            key="accessibility",
            score=access_score,
            weight=WEIGHTS["accessibility"],
            provenance=Provenance.SYNTHETIC,
            raw={
                "reachable_activated": inputs.shelters.reachable_activated_count,
                "activated_shelters": inputs.shelters.activated_count,
                "access_impaired_regions": sum(1 for r in priority if r.is_access_impaired),
            },
            notes=["Uses synthetic road-closure data; treat as indicative only."],
        )
    )

    # 4. Resource adequacy (planning ASSUMPTION — user-entered posture).
    response_capacity = (
        inputs.resources.response_teams * a.team_capacity + inputs.resources.boats * a.boat_capacity
    )
    if people_needing_shelter <= 0:
        resource_score = 1.0 if response_capacity > 0 else 0.0
    else:
        resource_score = _safe_ratio(response_capacity, people_needing_shelter)
    metrics.append(
        SubMetric(
            key="resource_adequacy",
            score=resource_score,
            weight=WEIGHTS["resource_adequacy"],
            provenance=Provenance.ASSUMPTION,
            raw={
                "response_capacity": response_capacity,
                "response_teams": inputs.resources.response_teams,
                "boats": inputs.resources.boats,
                "people_needing_shelter": round(people_needing_shelter),
                "allocation": inputs.resources.allocation,
            },
            notes=[
                f"Planning model: {a.team_capacity} people/team, {a.boat_capacity} people/boat."
            ],
        )
    )

    overall = round(100.0 * sum(m.score * m.weight for m in metrics), 1)

    # Coverage gaps: at-risk regions left out of the priority set.
    gaps = sorted(
        (
            CoverageGap(pcode=r.pcode, name=r.name, at_risk_population=round(r.at_risk_population))
            for r in inputs.regions
            if not r.is_priority and r.at_risk_population > 0
        ),
        key=lambda g: (-g.at_risk_population, g.pcode),
    )

    assumptions_used = [
        f"Displacement rate: {a.displacement_rate:.0%} of at-risk population needs shelter.",
        "At-risk population is areal-weighted (uniform density within a district).",
    ]
    if inputs.shelters.assumed_capacity_count > 0:
        assumptions_used.append("Some shelter capacities are planning assumptions.")
    assumptions_used.append("Resource posture is a user-entered planning input.")

    return ScoreResult(
        overall=overall,
        metrics=metrics,
        coverage_gaps=gaps,
        totals={
            "total_at_risk": round(total_at_risk),
            "covered_at_risk": round(covered_at_risk),
            "people_needing_shelter": round(people_needing_shelter),
            "uncovered_at_risk": round(total_at_risk - covered_at_risk),
        },
        uses_synthetic_data=True,  # accessibility always relies on synthetic closures
        assumptions_used=assumptions_used,
    )
