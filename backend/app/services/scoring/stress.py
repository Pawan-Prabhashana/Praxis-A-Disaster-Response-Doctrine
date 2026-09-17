"""The stress-test engine: seeded Monte Carlo around the pure scoring core.

Wraps the UNCHANGED Phase-4 ``score()`` — draws N perturbed input samples, scores
each, and aggregates into confidence bands + a robustness measure. Pure and
deterministic given a seed (no DB/HTTP), so aggregates are unit-testable and
``same playbook + config + seed → identical result``.

Future live/forecast scenarios: swap ``sample_inputs`` for a GloFAS-ensemble
provider that yields real forecast members — the aggregation is identical. That
seam is intentional; it is not implemented here.
"""

from __future__ import annotations

import random
import statistics

from pydantic import BaseModel, Field

from app.services.scoring.core import WEIGHTS, score
from app.services.scoring.models import ScoringInputs
from app.services.scoring.uncertainty import UncertaintyConfig, sample_inputs

STRESS_SCHEMA_VERSION = 1
_METRIC_KEYS: tuple[str, ...] = tuple(WEIGHTS.keys())
_HISTOGRAM_BINS = 20  # over the 0..100 score range


class HistogramBin(BaseModel):
    start: float
    end: float
    count: int


class DistributionSummary(BaseModel):
    """Summary statistics for one distribution of scores (0..100)."""

    mean: float
    median: float
    std: float
    p05: float
    p25: float
    p75: float
    p95: float
    min: float
    max: float
    histogram: list[HistogramBin] = Field(default_factory=list)


class Robustness(BaseModel):
    """Downside-focused robustness of the overall score under uncertainty."""

    worst_plausible: float  # p05 — "at least this in 95% of modeled conditions"
    probability_meets_target: float  # share of iterations with overall >= target
    target_score: float
    median: float


class StressResult(BaseModel):
    """Aggregated Monte Carlo result for one playbook."""

    version: int = STRESS_SCHEMA_VERSION
    seed: int
    n_iterations: int
    point_overall: float  # deterministic score (all params at point values)
    overall: DistributionSummary
    metrics: dict[str, DistributionSummary]
    robustness: Robustness
    config: UncertaintyConfig
    uses_synthetic_data: bool
    epistemic_note: str


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolation percentile (q in [0, 100]) of a sorted list."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (q / 100.0) * (len(sorted_values) - 1)
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    frac = rank - low
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * frac


def _histogram(values: list[float], lo: float = 0.0, hi: float = 100.0) -> list[HistogramBin]:
    width = (hi - lo) / _HISTOGRAM_BINS
    counts = [0] * _HISTOGRAM_BINS
    for v in values:
        idx = min(_HISTOGRAM_BINS - 1, max(0, int((v - lo) / width)))
        counts[idx] += 1
    return [
        HistogramBin(start=lo + i * width, end=lo + (i + 1) * width, count=c)
        for i, c in enumerate(counts)
    ]


def _summarize(values: list[float], *, with_histogram: bool = False) -> DistributionSummary:
    ordered = sorted(values)
    return DistributionSummary(
        mean=round(statistics.fmean(ordered), 2),
        median=round(_percentile(ordered, 50), 2),
        std=round(statistics.pstdev(ordered), 2) if len(ordered) > 1 else 0.0,
        p05=round(_percentile(ordered, 5), 2),
        p25=round(_percentile(ordered, 25), 2),
        p75=round(_percentile(ordered, 75), 2),
        p95=round(_percentile(ordered, 95), 2),
        min=round(ordered[0], 2),
        max=round(ordered[-1], 2),
        histogram=_histogram(ordered) if with_histogram else [],
    )


_EPISTEMIC_NOTE = (
    "Modeled (epistemic) uncertainty: Monte Carlo over documented parameter "
    "distributions, not measured forecast/observed spread. The seed event is "
    "historical, so GloFAS reanalysis has no ensemble. See docs/UNCERTAINTY.md."
)


def run_stress_test(
    base: ScoringInputs,
    config: UncertaintyConfig,
    *,
    n_iterations: int,
    seed: int,
) -> StressResult:
    """Run the seeded Monte Carlo and aggregate the distribution of scores."""
    rng = random.Random(seed)

    overall_samples: list[float] = []
    metric_samples: dict[str, list[float]] = {k: [] for k in _METRIC_KEYS}

    for _ in range(n_iterations):
        result = score(sample_inputs(base, config, rng))
        overall_samples.append(result.overall)
        for m in result.metrics:
            metric_samples[m.key].append(round(m.score * 100, 4))

    overall = _summarize(overall_samples, with_histogram=True)
    target = config.target_score
    meets = sum(1 for v in overall_samples if v >= target) / len(overall_samples)

    return StressResult(
        seed=seed,
        n_iterations=n_iterations,
        point_overall=score(base).overall,
        overall=overall,
        metrics={k: _summarize(v) for k, v in metric_samples.items()},
        robustness=Robustness(
            worst_plausible=overall.p05,
            probability_meets_target=round(meets, 4),
            target_score=target,
            median=overall.median,
        ),
        config=config,
        uses_synthetic_data=True,
        epistemic_note=_EPISTEMIC_NOTE,
    )
