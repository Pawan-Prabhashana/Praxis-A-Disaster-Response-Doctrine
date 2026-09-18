"""The pure after-action analysis core.

``build_after_action`` joins the strategy's PREDICTED district ranking (Praxis
at-risk) with the ACTUAL RECORDED impact (real DesInventar), computes a documented
composite impact, ranks both sides, and measures alignment. Pure and
deterministic: no DB/HTTP/clock/randomness. Every number traces to real inputs.
"""

from __future__ import annotations

from app.services.after_action.models import (
    IMPACT_WEIGHTS,
    AfterActionResult,
    AlignmentMeasure,
    DistrictComparison,
    DistrictOutcome,
    RegionPrediction,
)

# Recorded impact must be at least this many rank positions worse than predicted
# for a district to count as "under-prioritised".
_UNDER_PRIORITISED_DELTA = 2
_TOP_K = 3


def _normalise(value: float, maximum: float) -> float:
    """Min-max to [0, 1] (all components are non-negative, so the min is 0)."""
    return value / maximum if maximum > 0 else 0.0


def _composite(outcome: DistrictOutcome, maxes: dict[str, float]) -> float:
    """Weighted sum of min-max-normalised components, scaled to 0..100."""
    score = (
        IMPACT_WEIGHTS["deaths"] * _normalise(outcome.deaths, maxes["deaths"])
        + IMPACT_WEIGHTS["houses_destroyed"]
        * _normalise(outcome.houses_destroyed, maxes["houses_destroyed"])
        + IMPACT_WEIGHTS["affected"] * _normalise(outcome.affected, maxes["affected"])
    )
    return round(score * 100, 1)


def _ordinal_ranks(items: list[tuple[str, float]]) -> dict[str, int]:
    """Map key -> 1..n rank by value descending; ties broken by key for stability."""
    ordered = sorted(items, key=lambda kv: (-kv[1], kv[0]))
    return {key: i + 1 for i, (key, _) in enumerate(ordered)}


def _average_ranks(values: list[float]) -> list[float]:
    """Average ranks (1 = highest value), ties sharing the mean rank."""
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 0-based positions i..j -> ranks i+1..j+1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 2:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    va = sum((a[i] - ma) ** 2 for i in range(n))
    vb = sum((b[i] - mb) ** 2 for i in range(n))
    if va <= 0 or vb <= 0:
        return 0.0
    return cov / (va * vb) ** 0.5


def _spearman(predicted: list[float], recorded: list[float]) -> float:
    """Rank correlation via Pearson on average ranks (tie-safe)."""
    return _pearson(_average_ranks(predicted), _average_ranks(recorded))


def _alignment_label(rho: float) -> str:
    if rho >= 0.6:
        return "strong"
    if rho >= 0.2:
        return "moderate"
    if rho > -0.2:
        return "weak"
    return "inverted"


def build_after_action(
    scenario_slug: str,
    playbook_name: str,
    event_year: int | None,
    predictions: list[RegionPrediction],
    outcomes: list[DistrictOutcome],
) -> AfterActionResult:
    """Compare predicted at-risk ranking with recorded impact ranking."""
    outcome_by_pcode = {o.pcode: o for o in outcomes}

    # Component maxima across the district universe (for normalisation).
    maxes = {
        "deaths": max((o.deaths for o in outcomes), default=0),
        "houses_destroyed": max((o.houses_destroyed for o in outcomes), default=0),
        "affected": max((o.affected for o in outcomes), default=0),
    }

    # Predicted ranks (by at-risk) and recorded impact ranks (by composite) over
    # the full universe.
    predicted_rank = _ordinal_ranks([(p.pcode, p.at_risk_population) for p in predictions])
    composites = {
        p.pcode: _composite(
            outcome_by_pcode.get(p.pcode, DistrictOutcome(pcode=p.pcode, name=p.name)), maxes
        )
        for p in predictions
    }
    impact_rank = _ordinal_ranks(list(composites.items()))

    districts: list[DistrictComparison] = []
    for p in predictions:
        o = outcome_by_pcode.get(p.pcode, DistrictOutcome(pcode=p.pcode, name=p.name))
        p_rank = predicted_rank[p.pcode]
        i_rank = impact_rank[p.pcode]
        delta = p_rank - i_rank
        under = (
            o.has_data
            and o.deaths + o.houses_destroyed + o.affected > 0
            and (delta >= _UNDER_PRIORITISED_DELTA)
        )
        districts.append(
            DistrictComparison(
                pcode=p.pcode,
                name=p.name,
                at_risk_population=p.at_risk_population,
                is_priority=p.is_priority,
                predicted_rank=p_rank,
                deaths=o.deaths,
                affected=o.affected,
                houses_destroyed=o.houses_destroyed,
                incident_count=o.incident_count,
                has_data=o.has_data,
                impact_score=composites[p.pcode],
                impact_rank=i_rank,
                rank_delta=delta,
                under_prioritised=under,
                is_blind_spot=(not p.is_priority) and o.has_data and composites[p.pcode] > 0,
            )
        )

    districts.sort(key=lambda d: d.impact_rank)

    # Alignment on districts that actually recorded impact (ranking no-data
    # districts by "impact" is meaningless).
    with_data = [d for d in districts if d.has_data]
    if len(with_data) >= 2:
        rho = round(
            _spearman(
                [float(d.at_risk_population) for d in with_data],
                [d.impact_score for d in with_data],
            ),
            3,
        )
        k = min(_TOP_K, len(with_data))
        pred_top = {d.pcode for d in sorted(with_data, key=lambda d: -d.at_risk_population)[:k]}
        rec_top = {d.pcode for d in sorted(with_data, key=lambda d: -d.impact_score)[:k]}
        alignment = AlignmentMeasure(
            spearman=rho,
            label=_alignment_label(rho),
            top_k=k,
            top_k_overlap=len(pred_top & rec_top),
            n_districts=len(districts),
            n_with_data=len(with_data),
        )
    else:
        alignment = AlignmentMeasure(
            spearman=0.0,
            label="weak",
            top_k=0,
            top_k_overlap=0,
            n_districts=len(districts),
            n_with_data=len(with_data),
        )

    blind_spots = sorted(
        (d for d in districts if d.is_blind_spot),
        key=lambda d: -d.impact_score,
    )
    under_prioritised = [d for d in districts if d.under_prioritised]
    worst = max(
        under_prioritised,
        key=lambda d: (d.rank_delta, d.impact_score),
        default=None,
    )

    totals = {
        "deaths": sum(d.deaths for d in districts),
        "affected": sum(d.affected for d in districts),
        "houses_destroyed": sum(d.houses_destroyed for d in districts),
        "incident_count": sum(d.incident_count for d in districts),
        "districts_total": len(districts),
        "districts_with_data": len(with_data),
        "districts_prioritised": sum(1 for d in districts if d.is_priority),
    }

    return AfterActionResult(
        scenario_slug=scenario_slug,
        playbook_name=playbook_name,
        event_year=event_year,
        districts=districts,
        alignment=alignment,
        blind_spots=blind_spots,
        worst_under_prioritised=worst,
        totals=totals,
    )
