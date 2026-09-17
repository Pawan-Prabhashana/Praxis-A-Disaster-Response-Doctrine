"""Unit tests for the seeded Monte Carlo stress engine (pure, no DB)."""

from __future__ import annotations

from app.services.scoring.models import (
    RegionInput,
    ResourceInputs,
    ScoringInputs,
    ShelterInputs,
)
from app.services.scoring.stress import run_stress_test
from app.services.scoring.uncertainty import default_uncertainty_config


def _base() -> ScoringInputs:
    return ScoringInputs(
        regions=[
            RegionInput(
                pcode="LK-A",
                name="Alpha",
                population=100000,
                at_risk_population=60000,
                is_priority=True,
                is_access_impaired=True,
            ),
            RegionInput(
                pcode="LK-B",
                name="Beta",
                population=80000,
                at_risk_population=20000,
                is_priority=False,
                is_access_impaired=False,
            ),
        ],
        shelters=ShelterInputs(
            activated_count=20,
            capacity_known=0,
            capacity_assumed=6000,
            assumed_capacity_count=20,
            reachable_activated_count=12,
        ),
        resources=ResourceInputs(response_teams=15, boats=6, allocation="proportional_to_need"),
    )


def test_same_seed_is_reproducible() -> None:
    cfg = default_uncertainty_config()
    a = run_stress_test(_base(), cfg, n_iterations=400, seed=123)
    b = run_stress_test(_base(), cfg, n_iterations=400, seed=123)
    assert a.model_dump() == b.model_dump()


def test_different_seed_differs() -> None:
    cfg = default_uncertainty_config()
    a = run_stress_test(_base(), cfg, n_iterations=400, seed=1)
    b = run_stress_test(_base(), cfg, n_iterations=400, seed=2)
    assert a.overall.mean != b.overall.mean


def test_all_params_disabled_collapses_to_point() -> None:
    cfg = default_uncertainty_config()
    for p in cfg.params:
        p.enabled = False
    result = run_stress_test(_base(), cfg, n_iterations=200, seed=99)
    # With no perturbation every iteration equals the deterministic score.
    assert result.overall.std == 0.0
    assert result.overall.mean == result.point_overall
    assert result.overall.p05 == result.overall.p95 == result.point_overall


def test_band_is_ordered_and_robustness_consistent() -> None:
    cfg = default_uncertainty_config()
    result = run_stress_test(_base(), cfg, n_iterations=1000, seed=7)
    o = result.overall
    assert o.min <= o.p05 <= o.p25 <= o.median <= o.p75 <= o.p95 <= o.max
    assert o.std > 0
    assert result.robustness.worst_plausible == o.p05
    assert result.robustness.median == o.median
    assert 0.0 <= result.robustness.probability_meets_target <= 1.0
    # histogram present for the overall distribution, and every metric summarised
    assert len(o.histogram) == 20
    assert set(result.metrics) == {
        "population_coverage",
        "shelter_adequacy",
        "accessibility",
        "resource_adequacy",
    }


def test_uses_synthetic_flag_and_note() -> None:
    result = run_stress_test(_base(), default_uncertainty_config(), n_iterations=100, seed=5)
    assert result.uses_synthetic_data is True
    assert "epistemic" in result.epistemic_note.lower()
