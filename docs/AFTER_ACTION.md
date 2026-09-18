# After-action review — predicted vs. recorded (the Learn stage)

The Learn stage closes the Sense → Decide → Act → Learn loop. It compares a
strategy's **predicted** performance (Praxis at-risk ranking) against the
**actual recorded impact** of the real historical event, extracts lessons, and
persists them so doctrine improves across events.

## The framing — read this first (it is the honesty of the phase)

> **Predicted vs. recorded.** The recorded side is the **actual historical event
> impact** from DesInventar — the historical response baseline. It is **NOT** the
> outcome of executing a Praxis playbook. Praxis was not running in 2017.

So the comparison is a **retrospective benchmark**: *where the real event caused
recorded impact, did the strategy's at-risk ranking point there?* Every surface
(API payload `framing` field, UI banners, lesson text, this doc) states this, and
no wording implies the plan was executed or that these are its measured results.
Honest framing is deliberate — the value is in the gap it exposes, not in a claim
of success.

- Analysis core (pure): `backend/app/services/after_action/analysis.py`
- Recorded-outcomes gather (DB): `backend/app/services/after_action/gather.py`
- Lessons + guarded assessment: `backend/app/services/after_action/lessons.py`

## Data sources & flags

| Side | Source | Flag |
| ---- | ------ | ---- |
| **Recorded impact** | Real DesInventar `incident` rows (deaths / people affected / houses destroyed), aggregated per district, filtered to the scenario's **event year**. | **real** (`is_synthetic = false`) |
| **Predicted at-risk** | Praxis scoring: areal-weighted population ∩ flood extent per district (Phase 4). | **real** input, but the wider scoring uses **synthetic** (road closures) and **assumption** inputs — flagged. |

Recorded outcome numbers are parsed from the incident description the ingest
writes in a fixed format (`… Deaths: N, affected: N, houses destroyed: N.`), via a
documented SQL regex. A district with **no recorded incidents** in the window is
reported as **"no recorded data"** — never a fabricated zero-as-fact
(`has_data = false`).

## Metrics & formulas

### Recorded composite impact

Per district, three real components are combined. Because their raw scales differ
by orders of magnitude (deaths in the tens, people affected in the hundred-
thousands), each is **min-max normalised** across the district set first, then
weighted:

```
n(x)      = x / max(x over districts)          # 0..1, min is 0
composite = 100 × ( 0.5·n(deaths) + 0.3·n(houses_destroyed) + 0.2·n(affected) )
```

**Weights (documented):** loss of life is weighted highest (**0.5**), then homes
destroyed (**0.3**), then people affected / exposure (**0.2**). The raw components
are always shown alongside the composite, so the weighting hides nothing and a
reviewer can re-rank by any single component. Normalisation is **relative to the
district set** for this event (a within-event ranking, not a cross-event index).

### Predicted vs. recorded ranking

- **Predicted rank** — districts ranked by Praxis at-risk population (1 = highest).
- **Recorded impact rank** — districts ranked by composite impact (1 = highest).
- **rank_delta** = predicted_rank − impact_rank. `> 0` = **under-prioritised**
  (recorded worse than predicted); `< 0` = over-prioritised. A district is flagged
  **under-prioritised** when it has recorded impact and `rank_delta ≥ 2`.
- **Blind spot** — a district with recorded impact that is **not** in the
  strategy's priority set.

### Alignment measure

Two complementary, plain-language measures over the districts **with recorded
data**:

1. **Spearman rank correlation** between predicted at-risk rank and recorded
   impact rank (Pearson on average ranks, tie-safe; pure-Python, no SciPy).
   Bucketed: `≥ 0.6` strong · `0.2–0.6` moderate · `−0.2–0.2` weak · `< −0.2`
   **inverted**.
2. **Top-3 overlap** — how many of the three hardest-hit districts were in the
   strategy's predicted top-3 at-risk.

## What the seed event shows (a real, honest, loop-closing insight)

On the actual **2017** DesInventar data for the Kalu Ganga districts, the two
rankings are **inverted (Spearman ≈ −0.5)**:

- **Colombo** — Praxis's **#1** predicted at-risk district (largest flood-∩-
  population) — recorded **0 deaths** in 2017 (impact rank #5).
- **Ratnapura** — Praxis's **#5 / last** predicted at-risk district — recorded the
  **most deaths (84)** (impact rank #2). It is landslide-prone hill country the
  flood-inundation-area model structurally under-weights.

The lesson writes itself: **flood-inundation at-risk population is not where people
actually died.** Recorded-impact history — especially loss of life and landslide
susceptibility — should be weighted alongside flood exposure. This is exactly the
kind of doctrine correction the Learn stage exists to surface, and it is real, not
engineered.

## Lessons model

Structured **lessons** are deterministic (every number traces to the analysis by
construction):

- **alignment** — the Spearman/overlap finding (severity scales with the label;
  *inverted* → critical).
- **under_prioritised** — the district most under-ranked relative to its recorded
  impact (the headline miss).
- **over_prioritised** — the top predicted district whose recorded impact was low.
- **blind_spot** — recorded-impact districts outside the priority set (for focused
  strategies).
- **loop_closure** — the "for next time" takeaway.

A short narrative **assessment** paragraph is optionally **LLM-narrated**, reusing
the Phase-6 trust pipeline **exactly**: real facts in → a **numeric-consistency
guard** checks every number against the analysis → on any drift it falls back to
the deterministic template. It **works with no key** (template), and no test calls
a real API. See [`BRIEF.md`](BRIEF.md) for the guard mechanics.

## Persistence

Each review persists (migration `0006`, `after_action` table) the analysis
snapshot (`result`) and the lessons + assessment (`lessons`), with optional refs to
the brief / stress run — reproducible and auditable.

## Endpoints

- `GET  /api/v1/scenarios/{slug}/recorded-outcomes` — aggregated real impact per
  district (+ the `framing` line, `is_synthetic = false`).
- `POST /api/v1/scenarios/{slug}/playbooks/{id}/after-action` — build + persist.
- `GET  …/after-actions` and `…/after-actions/{id}` — list / fetch.

## The future-live seam (shape, not implemented)

For a **live** event, "actual outcomes" would stream from real response reporting
rather than a historical loss inventory. The analysis core already takes plain
`DistrictOutcome` records; swapping the DesInventar gather for a live-outcomes
provider yields the same predicted-vs-recorded analysis with no change to the core.
That seam is intentional and documented; it is not implemented here.
