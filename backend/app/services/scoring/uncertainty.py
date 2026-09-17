"""Uncertainty model for stress-testing playbooks.

The seed event is HISTORICAL, so there is no forecast/observed ensemble to draw
on. Praxis models **epistemic** (assumption/modeling) uncertainty by perturbing
the scoring inputs over documented distributions — Monte Carlo over parameters,
NOT measured meteorological spread. Each parameter carries its distribution, a
stated basis, and an honesty class (see docs/UNCERTAINTY.md).

Everything here is pure and deterministic given a seeded ``random.Random``.
"""

from __future__ import annotations

import random
from enum import StrEnum

from pydantic import BaseModel

from app.services.scoring.models import ScoringInputs

UNCERTAINTY_SCHEMA_VERSION = 1


class ParamClass(StrEnum):
    """Honesty class of an uncertainty parameter (surfaced in the UI)."""

    REAL_UNCERTAINTY = "real_uncertainty"  # genuine error on real data
    ASSUMPTION = "assumption"  # planning assumption / decision variable
    SYNTHETIC_DERIVED = "synthetic_derived"  # derived from flagged sample data


class DistKind(StrEnum):
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"
    CONSTANT = "constant"


class Distribution(BaseModel):
    """A 1-D sampling distribution. ``mode`` is used by triangular/constant."""

    kind: DistKind
    low: float = 0.0
    high: float = 1.0
    mode: float = 1.0

    def draw(self, rng: random.Random) -> float:
        if self.kind is DistKind.TRIANGULAR:
            return rng.triangular(self.low, self.high, self.mode)
        if self.kind is DistKind.UNIFORM:
            return rng.uniform(self.low, self.high)
        return self.mode

    def summary(self) -> str:
        if self.kind is DistKind.TRIANGULAR:
            return f"triangular(min={self.low:g}, mode={self.mode:g}, max={self.high:g})"
        if self.kind is DistKind.UNIFORM:
            return f"uniform({self.low:g}, {self.high:g})"
        return f"constant({self.mode:g})"


class UncertaintyParam(BaseModel):
    """One perturbed input: its distribution, basis, honesty class, and toggle."""

    key: str
    label: str
    param_class: ParamClass
    distribution: Distribution
    basis: str
    enabled: bool = True


class UncertaintyConfig(BaseModel):
    """The full, versioned set of uncertainty parameters + robustness target."""

    version: int = UNCERTAINTY_SCHEMA_VERSION
    target_score: float = 60.0
    params: list[UncertaintyParam]

    def by_key(self) -> dict[str, UncertaintyParam]:
        return {p.key: p for p in self.params}


# --- Parameter keys (stable identifiers) ------------------------------------
DISPLACEMENT_RATE = "displacement_rate"
AT_RISK_POPULATION = "at_risk_population"
RESOURCE_EFFECTIVENESS = "resource_effectiveness"
SHELTER_CAPACITY = "shelter_capacity"
CLOSURE_REALIZATION = "closure_realization"


def default_uncertainty_config() -> UncertaintyConfig:
    """Competition-ready defaults. Every value is documented in UNCERTAINTY.md."""
    return UncertaintyConfig(
        target_score=60.0,
        params=[
            UncertaintyParam(
                key=DISPLACEMENT_RATE,
                label="Displacement rate",
                param_class=ParamClass.ASSUMPTION,
                distribution=Distribution(kind=DistKind.TRIANGULAR, low=0.08, mode=0.15, high=0.30),
                basis=(
                    "Share of at-risk population needing shelter. Planning assumption informed by "
                    "IFRC/UNHCR/Sphere rules of thumb; the displaced share varies widely by event. "
                    "Mode = Phase-4 point value (0.15). No single authoritative value."
                ),
            ),
            UncertaintyParam(
                key=AT_RISK_POPULATION,
                label="At-risk population estimate",
                param_class=ParamClass.REAL_UNCERTAINTY,
                distribution=Distribution(kind=DistKind.TRIANGULAR, low=0.80, mode=1.0, high=1.25),
                basis=(
                    "Multiplicative error on the areal-weighted at-risk estimate (uniform-density "
                    "assumption over the district/flood overlap). A systematic +/-20-25% band: a "
                    "planning estimate of estimation error on real inputs, not a measured error."
                ),
            ),
            UncertaintyParam(
                key=RESOURCE_EFFECTIVENESS,
                label="Resource effectiveness",
                param_class=ParamClass.ASSUMPTION,
                distribution=Distribution(kind=DistKind.TRIANGULAR, low=0.6, mode=1.0, high=1.2),
                basis=(
                    "Multiplier on people served per team/boat. Planning assumption, no source — "
                    "real-world effectiveness is uncertain and context-dependent."
                ),
            ),
            UncertaintyParam(
                key=SHELTER_CAPACITY,
                label="Shelter capacity",
                param_class=ParamClass.ASSUMPTION,
                distribution=Distribution(kind=DistKind.TRIANGULAR, low=0.7, mode=1.0, high=1.3),
                basis=(
                    "Multiplier on assumed shelter capacity (OSM records none). Spread reflects "
                    "Sphere minimum-space ranges; planning assumption."
                ),
            ),
            UncertaintyParam(
                key=CLOSURE_REALIZATION,
                label="Road-closure severity",
                param_class=ParamClass.SYNTHETIC_DERIVED,
                distribution=Distribution(kind=DistKind.TRIANGULAR, low=0.5, mode=1.0, high=1.5),
                basis=(
                    "Multiplier on how many activated shelters are cut off. Road closures are "
                    "SYNTHETIC sample data, so this varies how many bind; always flagged synthetic."
                ),
            ),
        ],
    )


def _sampled(config_by_key: dict[str, UncertaintyParam], key: str, rng: random.Random) -> float:
    """Draw a value for a param, or its identity (1.0) when disabled/absent."""
    param = config_by_key.get(key)
    if param is None or not param.enabled:
        return 1.0
    return param.distribution.draw(rng)


def sample_inputs(
    base: ScoringInputs, config: UncertaintyConfig, rng: random.Random
) -> ScoringInputs:
    """Return a perturbed copy of ``base`` for one Monte Carlo iteration.

    Each enabled parameter is drawn once (correlated across regions where it is a
    systematic factor); disabled parameters collapse to their point values, so
    the engine reduces exactly to the deterministic core.
    """
    by_key = config.by_key()

    disp_param = by_key.get(DISPLACEMENT_RATE)
    displacement = (
        disp_param.distribution.draw(rng)
        if disp_param and disp_param.enabled
        else base.assumptions.displacement_rate
    )
    ar_mult = _sampled(by_key, AT_RISK_POPULATION, rng)
    res_mult = _sampled(by_key, RESOURCE_EFFECTIVENESS, rng)
    cap_mult = _sampled(by_key, SHELTER_CAPACITY, rng)
    closure_mult = _sampled(by_key, CLOSURE_REALIZATION, rng)

    regions = [
        r.model_copy(update={"at_risk_population": r.at_risk_population * ar_mult})
        for r in base.regions
    ]

    activated = base.shelters.activated_count
    unreachable = activated - base.shelters.reachable_activated_count
    new_unreachable = min(activated, max(0, round(unreachable * closure_mult)))
    shelters = base.shelters.model_copy(
        update={
            "capacity_assumed": base.shelters.capacity_assumed * cap_mult,
            "reachable_activated_count": activated - new_unreachable,
        }
    )

    assumptions = base.assumptions.model_copy(
        update={
            "displacement_rate": displacement,
            "team_capacity": max(1, round(base.assumptions.team_capacity * res_mult)),
            "boat_capacity": max(1, round(base.assumptions.boat_capacity * res_mult)),
        }
    )

    return base.model_copy(
        update={"regions": regions, "shelters": shelters, "assumptions": assumptions}
    )
