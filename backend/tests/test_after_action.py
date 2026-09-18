"""Unit tests for the pure after-action analysis core."""

from __future__ import annotations

from app.services.after_action.analysis import build_after_action
from app.services.after_action.models import DistrictOutcome, RegionPrediction
from tests.after_action_fixtures import OUTCOMES, PREDICTIONS


def _run(preds=None, outs=None):
    return build_after_action(
        "2017-sw-monsoon-kalu-ganga", "Wide coverage", 2017, preds or PREDICTIONS, outs or OUTCOMES
    )


def test_alignment_is_inverted_on_seed_shaped_data() -> None:
    r = _run()
    # Predicted at-risk ranking is inverted vs recorded impact (the headline).
    assert r.alignment.spearman == -0.5
    assert r.alignment.label == "inverted"
    assert r.alignment.top_k == 3
    assert r.alignment.top_k_overlap == 2
    assert r.alignment.n_with_data == 5


def test_colombo_over_ratnapura_under_prioritised() -> None:
    r = _run()
    by = {d.pcode: d for d in r.districts}
    # Colombo: predicted #1 at-risk, recorded 0 deaths -> lowest impact rank.
    assert by["LK11"].predicted_rank == 1
    assert by["LK11"].impact_rank == 5
    assert by["LK11"].deaths == 0
    # Ratnapura: predicted last, but recorded the most deaths -> under-prioritised.
    assert by["LK91"].predicted_rank == 5
    assert by["LK91"].under_prioritised is True
    assert r.worst_under_prioritised is not None
    assert r.worst_under_prioritised.pcode == "LK91"


def test_composite_is_normalised_and_weighted() -> None:
    r = _run()
    by = {d.pcode: d for d in r.districts}
    # Composite = 0.5*deaths_n + 0.3*houses_n + 0.2*affected_n, x100.
    # Ratnapura: deaths max (84) -> 0.5*1.0; houses 222/799; affected 148041/202666.
    expected = round((0.5 * 1.0 + 0.3 * (222 / 799) + 0.2 * (148041 / 202666)) * 100, 1)
    assert by["LK91"].impact_score == expected
    # Colombo recorded 0 deaths -> low composite.
    assert by["LK11"].impact_score < 10


def test_no_recorded_data_district_is_not_impact_or_blind_spot() -> None:
    preds = [
        *PREDICTIONS,
        RegionPrediction(
            pcode="LK72", name="Polonnaruwa", at_risk_population=5000, is_priority=False
        ),
    ]
    outs = [*OUTCOMES, DistrictOutcome(pcode="LK72", name="Polonnaruwa", has_data=False)]
    r = _run(preds, outs)
    poll = next(d for d in r.districts if d.pcode == "LK72")
    assert poll.has_data is False
    assert poll.impact_score == 0.0
    assert poll.under_prioritised is False
    assert poll.is_blind_spot is False
    # A no-data district is excluded from the alignment measure.
    assert r.alignment.n_with_data == 5
    assert r.totals["districts_with_data"] == 5


def test_blind_spot_when_high_impact_district_not_prioritised() -> None:
    # A "focused" strategy that drops Ratnapura from the priority set.
    preds = [p.model_copy(update={"is_priority": p.pcode != "LK91"}) for p in PREDICTIONS]
    r = build_after_action("s", "Focused", 2017, preds, OUTCOMES)
    ratna = next(d for d in r.districts if d.pcode == "LK91")
    assert ratna.is_blind_spot is True
    assert any(b.pcode == "LK91" for b in r.blind_spots)
