"""Unit tests for the pure, deterministic scoring core (no DB, no network)."""

from __future__ import annotations

from app.services.scoring.core import WEIGHTS, score
from app.services.scoring.models import (
    Provenance,
    RegionInput,
    ResourceInputs,
    ScoringInputs,
    ShelterInputs,
)


def _inputs() -> ScoringInputs:
    return ScoringInputs(
        regions=[
            RegionInput(
                pcode="LK-A",
                name="Alpha",
                population=1000,
                at_risk_population=800,
                is_priority=True,
                is_access_impaired=True,
            ),
            RegionInput(
                pcode="LK-B",
                name="Beta",
                population=1000,
                at_risk_population=200,
                is_priority=False,
                is_access_impaired=False,
            ),
        ],
        shelters=ShelterInputs(
            activated_count=2,
            capacity_known=60,
            capacity_assumed=60,
            assumed_capacity_count=1,
            reachable_activated_count=1,
        ),
        resources=ResourceInputs(response_teams=1, boats=0, allocation="even"),
    )


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_overall_and_submetrics_are_exact() -> None:
    result = score(_inputs())

    by_key = {m.key: m for m in result.metrics}
    # population coverage = 800 / 1000
    assert by_key["population_coverage"].score == 0.8
    # people needing shelter = 0.15 * 800 = 120; capacity 120 → adequacy 1.0
    assert by_key["shelter_adequacy"].score == 1.0
    # reachable 1 / activated 2
    assert by_key["accessibility"].score == 0.5
    # capacity 1*500=500 vs need 120 → 1.0
    assert by_key["resource_adequacy"].score == 1.0

    # 100 * (0.8*0.35 + 1.0*0.30 + 0.5*0.15 + 1.0*0.20) = 85.5
    assert result.overall == 85.5


def test_provenance_flags_propagate() -> None:
    by_key = {m.key: m for m in score(_inputs()).metrics}
    assert by_key["population_coverage"].provenance is Provenance.REAL
    assert by_key["accessibility"].provenance is Provenance.SYNTHETIC
    # capacity assumption used → shelter metric flagged assumption
    assert by_key["shelter_adequacy"].provenance is Provenance.ASSUMPTION
    assert by_key["resource_adequacy"].provenance is Provenance.ASSUMPTION


def test_coverage_gaps_list_uncovered_at_risk_regions() -> None:
    result = score(_inputs())
    assert [g.pcode for g in result.coverage_gaps] == ["LK-B"]
    assert result.coverage_gaps[0].at_risk_population == 200
    assert result.totals["uncovered_at_risk"] == 200


def test_deterministic() -> None:
    a = score(_inputs())
    b = score(_inputs())
    assert a.model_dump() == b.model_dump()


def test_empty_strategy_scores_zero_coverage() -> None:
    empty = ScoringInputs(
        regions=[
            RegionInput(
                pcode="LK-A",
                name="Alpha",
                population=1000,
                at_risk_population=800,
                is_priority=False,
                is_access_impaired=False,
            )
        ],
        shelters=ShelterInputs(
            activated_count=0,
            capacity_known=0,
            capacity_assumed=0,
            assumed_capacity_count=0,
            reachable_activated_count=0,
        ),
        resources=ResourceInputs(response_teams=0, boats=0, allocation="even"),
    )
    result = score(empty)
    by_key = {m.key: m for m in result.metrics}
    assert by_key["population_coverage"].score == 0.0
    assert result.overall == 0.0
    assert result.coverage_gaps[0].pcode == "LK-A"
