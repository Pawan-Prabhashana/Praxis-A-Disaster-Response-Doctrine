# Uncertainty & the stress-test engine

Praxis's deterministic scorecard (see [`SCORING.md`](SCORING.md)) answers *"how
good is this playbook against the best point estimate of the situation?"*. The
**stress-test engine** answers the harder, more honest question: *"how good is it
across the range of situations we cannot rule out — and does it still hold up on a
bad day?"*

This document is the authoritative reference for **what kind of uncertainty
Praxis models, why, every parameter and its basis, and how robustness is
measured**.

- Uncertainty model + sampler: `backend/app/services/scoring/uncertainty.py`
- Monte Carlo engine: `backend/app/services/scoring/stress.py`
- Pure scoring core (reused UNCHANGED): `backend/app/services/scoring/core.py`

## The honest framing: epistemic, not forecast, uncertainty

**This is the single most important thing to understand about this feature, and it
is stated in the code, the API payloads, and the UI.**

The seed scenario — the **2017 south-west-monsoon Kalu Ganga floods** — is a
**historical** event. Its flood extent is an observed UNOSAT/NRC polygon, and the
hydrology behind it (GloFAS) is a **reanalysis**: a single deterministic
reconstruction of what happened. **There is no forecast ensemble, no spread of
measured meteorological outcomes to draw on.**

So Praxis does **not** manufacture fake weather uncertainty. Instead it models the
uncertainty that genuinely exists in a planning exercise like this:

| | |
| --- | --- |
| **Aleatoric** (what Praxis does **NOT** claim to have) | Irreducible, measured randomness in the physical event — e.g. spread across members of a live GloFAS flood-forecast ensemble. Requires a forecast product Praxis is not ingesting for a historical event. |
| **Epistemic** (what Praxis **DOES** model) | Uncertainty in our *knowledge and assumptions*: the displaced share, the true at-risk count behind an areal-weighting estimate, how effective a team really is, how much synthetic road-closure data would bind. Reducible in principle with better data; here it is made explicit and sampled. |

Praxis performs **Monte Carlo over documented parameter distributions** — a
principled perturbation of the decision/environment inputs — and reports the
resulting spread as **modeled (epistemic)** uncertainty. Every result payload
carries an `epistemic_note` and `uses_synthetic_data` flag, and the UI leads with
an epistemic banner. **Modeled parameter uncertainty is never presented as
observed or forecast uncertainty.**

### The forecast-ensemble seam (built, not implemented)

The engine is deliberately structured so a future live scenario can add real
forecast spread **without touching the aggregation**. `run_stress_test` draws each
iteration's inputs from `sample_inputs(base, config, rng)`. Swapping that single
call for a provider that yields **real GloFAS-ensemble members** turns the same
histogram/band/robustness machinery into genuine aleatoric forecast uncertainty.
That seam is intentional and documented; it is **not** implemented in this phase.

## Parameters

Each parameter carries a **distribution**, a **stated basis** (citation or an
explicit "no source"), and an **honesty class** surfaced as a badge in the UI.

| Class (`param_class`) | Badge | Meaning |
| --------------------- | ----- | ------- |
| `real_uncertainty` | *estimation error* | Genuine error band on a value derived from **real** data. |
| `assumption` | *assumption* | A planning assumption or user-entered decision variable, not measured. |
| `synthetic_derived` | *sample-derived* | Driven by flagged **synthetic** sample data (road closures). |

Defaults come from `default_uncertainty_config()` (schema version 1). All are
**editable and individually toggleable** in the UI; disabling a parameter collapses
it to its point value, so the engine reduces **exactly** to the deterministic core.

### 1. `displacement_rate` — *assumption*

- **Distribution:** `triangular(min 0.08, mode 0.15, max 0.30)` — sampled as a
  direct value (replaces the point `displacement_rate`).
- **Drives:** people needing shelter → shelter adequacy & resource adequacy.
- **Basis:** Share of the at-risk population that needs shelter. Planning
  assumption informed by IFRC/UNHCR/Sphere rules of thumb; the displaced share
  varies widely by event and warning time. Mode = the Phase-4 point value (0.15).
  **No single authoritative value.**

### 2. `at_risk_population` — *real_uncertainty*

- **Distribution:** `triangular(min 0.80, mode 1.00, max 1.25)` — a multiplier on
  the areal-weighted at-risk estimate, applied **correlated across all regions**
  in an iteration (a systematic, not per-region, error).
- **Drives:** population coverage denominators, shelter/resource need.
- **Basis:** Multiplicative error on the at-risk estimate, which rests on a
  **uniform-population-density** assumption over the district/flood overlap (see
  `SCORING.md`). A systematic **+/-20-25%** band represents a planning estimate of
  the *estimation error on real inputs* — not a measured error, hence a band, not a
  point claim.

### 3. `resource_effectiveness` — *assumption*

- **Distribution:** `triangular(min 0.60, mode 1.00, max 1.20)` — a multiplier on
  `team_capacity` and `boat_capacity` (rounded to ≥1 whole person/unit).
- **Drives:** resource adequacy.
- **Basis:** People effectively served per team/boat. Planning assumption, **no
  source** — real-world effectiveness is uncertain and context-dependent (terrain,
  fatigue, access).

### 4. `shelter_capacity` — *assumption*

- **Distribution:** `triangular(min 0.70, mode 1.00, max 1.30)` — a multiplier on
  the **assumed** shelter capacity only.
- **Drives:** shelter adequacy.
- **Basis:** OSM records no capacity for the seed shelters, so scoring uses an
  assumed capacity (`SCORING.md`). The spread reflects Sphere minimum-space ranges;
  a planning assumption.

### 5. `closure_realization` — *synthetic_derived*

- **Distribution:** `triangular(min 0.50, mode 1.00, max 1.50)` — a multiplier on
  the count of activated shelters cut off by closed roads (clamped to
  `[0, activated]`, rounded).
- **Drives:** accessibility.
- **Basis:** Road closures are **synthetic sample data**. This parameter varies how
  many closures actually bind; the metric it feeds is **always** flagged synthetic.

## How a sample is drawn

For each iteration (`sample_inputs`):

1. Draw each **enabled** parameter once from its distribution using the seeded RNG.
   Disabled/absent parameters use their **identity** (the point `displacement_rate`,
   or a `×1.0` multiplier), so the iteration equals the deterministic core.
2. Apply the `at_risk_population` multiplier to **every** region (correlated).
3. Scale assumed shelter capacity; recompute reachable shelters from the perturbed
   closure count.
4. Set the sampled `displacement_rate`; scale team/boat capacity by
   `resource_effectiveness`.
5. Call the **unchanged** `score(inputs)` on the perturbed copy.

The base inputs are never mutated — each iteration works on a `model_copy`.

## Robustness — a downside-focused measure

Averages hide fragility. A strategy with a great mean can still collapse on a bad
day. So robustness is reported on the **downside**:

| Measure | Definition |
| ------- | ---------- |
| **Worst-plausible** | `p05` of the overall-score distribution — *"at least this good in ~95% of modeled conditions."* |
| **Probability of meeting target** | Share of iterations with `overall ≥ target_score` (default target **60**, editable). |
| **Median** | `p50` — the typical outcome, distinct from the point score. |
| **90% band** | `p05 … p95` — the middle-90% spread reported alongside the median. |

Percentiles use **linear interpolation** on the sorted samples. The overall
distribution is also returned as a 20-bin histogram over the 0–100 range.

### Robust winner ≠ point winner

The most valuable thing this engine surfaces is a **reversal**: when the strategy
that wins on the deterministic scorecard is **not** the one you'd trust on a bad
day. The seed data produces a genuine example (see the demo pair in the README) —
a wide-coverage strategy scores highest at the point estimate but has a lower
worst-plausible floor than a more focused, better-resourced strategy. Compare mode
detects and highlights this automatically.

## Reproducibility

Every run is **fully reproducible**. `run_stress_test(..., seed=S)` seeds a single
`random.Random(S)`; the **same playbook + config + seed → byte-identical
aggregates** (unit- and integration-tested). The API accepts an optional `seed`;
when omitted it generates one with `secrets` and **persists it** on the
`stress_run` row alongside the config, so any stored run can be replayed exactly.

## What is stored

The `stress_run` table stores the **config**, `n_iterations`, `seed`, and the
**aggregated** result (summaries + histogram bins) as JSONB — **not** the raw
per-iteration samples. Runs are therefore compact and replayable from the seed.

## Scope

This phase models epistemic parameter uncertainty only. It does **not** ingest a
forecast ensemble, and it does **not** attempt after-action calibration of these
distributions against observed outcomes (a Phase-6 "Learn" concern). The
distributions are defensible planning ranges, each labeled with its basis and
honesty class — never invented empirical claims.
