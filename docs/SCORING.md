# Playbook scoring — formulas, inputs, and provenance

Praxis scores a response strategy (a **playbook**) against a scenario's **real**
data with a **deterministic** function: the same levers + scenario always yield
the same scorecard. This document is the authoritative reference for every metric
— its formula, its inputs, and how synthetic/assumption influences are flagged.

- Pure core: `backend/app/services/scoring/core.py` (`score(inputs) → ScoreResult`)
- Input resolver (PostGIS): `backend/app/services/scoring/gather.py`
- Types: `backend/app/services/scoring/models.py`

Every metric returns a **sub-score in `[0, 1]`**, a **weight**, the **raw numbers**
behind it, and a **provenance** tag:

| Provenance | Meaning |
| ---------- | ------- |
| `real` | Derived only from real ingested data. |
| `synthetic` | Derived (partly) from flagged sample data (road closures). |
| `assumption` | Derived from a documented planning assumption or a user-entered decision variable. |

The UI renders these tags on every metric (badge + raw numbers), so a commander
always sees what a number rests on.

## Shared quantities

**At-risk population per district** (real data; areal-weighting *assumption*):

```
at_risk(d) = population(d) × ( area(d ∩ flood_extent) / area(d) )
```

- `population(d)` — COD-PS district population (real).
- `flood_extent` — the scenario's real observed flood polygon (UNOSAT/NRC).
- Areas via `ST_Area(geography)` on the intersection. The fraction assumes
  **uniform population density within a district** — a stated modelling
  assumption, not fabricated data. (Population is only published to district
  level, so scoring is at admin level 2.)

```
total_at_risk    = Σ at_risk(d)  over all flood-affected districts
covered_at_risk  = Σ at_risk(d)  over priority districts (a lever)
people_needing_shelter = displacement_rate × covered_at_risk
```

## Assumptions (constants)

| Assumption | Default | Used by |
| ---------- | ------- | ------- |
| `displacement_rate` | 0.15 | shelter & resource need |
| `team_capacity` | 500 people/team | resource adequacy |
| `boat_capacity` | 200 people/boat | resource adequacy |
| `closed_road_buffer_m` | 500 m | accessibility |
| `assumed_shelter_capacity` | school 500 · college 800 · community_centre 200 · default 300 | shelter adequacy |

All shelters in the seed data have **no capacity recorded in OSM**, so activated
capacity uses the planning assumption above; the number of shelters that relied
on the assumption is reported and the metric is flagged `assumption`.

## Metrics & weights

Overall score: `100 × Σ (sub_score × weight)`, weights summing to 1.0.

| Metric | Weight | Provenance |
| ------ | -----: | ---------- |
| Population coverage | 0.35 | real |
| Shelter adequacy | 0.30 | real / assumption* |
| Accessibility | 0.15 | synthetic |
| Resource adequacy | 0.20 | assumption |

\* `assumption` whenever any activated shelter used an assumed capacity.

### 1. Population coverage — weight 0.35 (real)

```
score = clamp01( covered_at_risk / total_at_risk )
```

Share of the flood-affected population the strategy prioritises. Raw: covered,
total, priority-region count.

### 2. Shelter adequacy — weight 0.30 (real + capacity assumption)

```
activated_capacity = Σ capacity(s)          for activated shelters with real capacity
                   + Σ assumed_capacity(s)  for activated shelters without capacity
score = clamp01( activated_capacity / people_needing_shelter )   (1.0 if need = 0)
```

Raw: activated_capacity, capacity_known, capacity_assumed, assumed_capacity_count,
people_needing_shelter, activated_shelters. Flagged `assumption` when
`assumed_capacity_count > 0`, with a note stating how many shelters used it.

### 3. Accessibility — weight 0.15 (SYNTHETIC)

```
score = clamp01( reachable_activated / activated_shelters )
reachable = activated shelters NOT within closed_road_buffer_m of a closed road
```

Road **closures are synthetic sample data**, so this metric is always flagged
`synthetic` ("treat as indicative only"). Reachability uses a planar
`ST_DWithin` (GIST-indexed) with the buffer converted to degrees. Raw:
reachable_activated, activated_shelters, access_impaired priority regions.

### 4. Resource adequacy — weight 0.20 (planning ASSUMPTION)

```
response_capacity = teams × team_capacity + boats × boat_capacity
score = clamp01( response_capacity / people_needing_shelter )   (1.0 if need = 0)
```

Resource posture (teams, boats, allocation) is a **user-entered planning
decision variable**, not real data — always flagged `assumption`. Raw:
response_capacity, teams, boats, people_needing_shelter, allocation.

### Coverage gaps (surfaced, not weighted)

At-risk districts **not** in the priority set, sorted by at-risk population
descending. This exposes each strategy's blind spots (its uncovered population is
also `totals.uncovered_at_risk`). Complementary to population coverage, so it is
not double-counted.

## Determinism & the Phase 5 seam

`score(ScoringInputs) → ScoreResult` is pure: no randomness, DB, HTTP, or clock.
Identical inputs → identical output (unit-tested in
`backend/tests/test_scoring_core.py`).

Phase 5 (uncertainty) will **perturb `ScoringInputs`** — e.g. sample
`displacement_rate`, `at_risk_population`, or resource effectiveness across a
principled range — and call the same `score` over the distribution to produce
confidence bands. No change to the core is required. (The seed event is
historical, so GloFAS reanalysis has no ensemble spread; uncertainty comes from
parameter perturbation, not a forecast ensemble.)

## Performance note

Per-scenario region facts (at-risk, access-impaired) are heavy to compute
(`ST_Intersection` over the detailed flood polygon) but **lever-independent**, so
they are memoised per scenario (`_REGION_FACTS_CACHE`) and warmed at startup.
Live preview scoring is then sub-100 ms. Restart the API after a re-`data-load`.
