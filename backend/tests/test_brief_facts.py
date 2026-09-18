"""Unit tests for the brief facts assembler (the trust boundary)."""

from __future__ import annotations

from tests.brief_fixtures import make_facts


def test_facts_carry_exact_scenario_and_strategy() -> None:
    facts = make_facts()
    assert facts.scenario.slug == "2017-sw-monsoon-kalu-ganga"
    assert facts.strategy.name == "Wide coverage"
    # Two priority districts, sorted by at-risk descending.
    assert facts.strategy.priority_region_count == 2
    assert [r.name for r in facts.strategy.priority_regions] == ["Colombo", "Kalutara"]
    assert facts.strategy.response_teams == 260
    assert facts.strategy.displacement_rate_pct == 15


def test_scorecard_numbers_match_scoring_core() -> None:
    facts = make_facts()
    # covered = 367562 + 181445; total adds Galle 108294.
    assert facts.scorecard.covered_at_risk == 549_007
    assert facts.scorecard.total_at_risk == 549_007 + 108_294
    # Overall is the weighted core score (0..100).
    assert 0.0 <= facts.scorecard.overall <= 100.0
    keys = {m.key for m in facts.scorecard.metrics}
    assert keys == {
        "population_coverage",
        "shelter_adequacy",
        "accessibility",
        "resource_adequacy",
    }


def test_coverage_gaps_and_synthetic_flag_preserved() -> None:
    facts = make_facts()
    # Galle is at-risk but not prioritised -> a coverage gap.
    assert any(g.name == "Galle" for g in facts.coverage_gaps)
    # Accessibility rests on synthetic closures -> flagged influence + global flag.
    assert facts.uses_synthetic_data is True
    assert any("synthetic" in s.lower() for s in facts.synthetic_influences)


def test_no_robustness_when_no_stress_run() -> None:
    facts = make_facts()
    assert facts.robustness is None
