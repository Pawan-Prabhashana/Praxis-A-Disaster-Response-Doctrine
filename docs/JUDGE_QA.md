# Judge Q&A — the hard questions

Crisp answers to the questions Praxis is most likely to be probed on. Deeper
detail is in [`SCORING.md`](SCORING.md), [`UNCERTAINTY.md`](UNCERTAINTY.md),
[`BRIEF.md`](BRIEF.md), [`AFTER_ACTION.md`](AFTER_ACTION.md), and
[`DATA_SOURCES.md`](DATA_SOURCES.md).

### How does the scoring work? Is it just made-up weights?

A playbook is scored by a **pure, deterministic** function on real data —
identical inputs always give an identical scorecard. Four metrics, explicit
documented weights (population coverage 0.35, shelter adequacy 0.30, resource
adequacy 0.20, accessibility 0.15). Each metric returns a 0–1 sub-score, the raw
numbers behind it, and a **provenance tag** (real / synthetic / assumption) shown
in the UI. At-risk population is real: district population ∩ the observed flood
polygon, areal-weighted. Nothing is hidden — the raw inputs and the flags are all
on screen. See `SCORING.md`.

### Epistemic vs. aleatoric uncertainty — why perturbation and not a GloFAS ensemble?

The 2017 event is **historical**. GloFAS reanalysis for a past event is a single
deterministic reconstruction — there is **no forecast ensemble** to sample. So we
do **not** fake meteorological spread. Instead we model **epistemic** uncertainty:
a seeded Monte Carlo over documented distributions of the *decision/environment
parameters* (displacement rate, at-risk estimate, resource effectiveness, shelter
capacity, road-closure severity). Every result is labeled "modeled (epistemic)
uncertainty, not measured forecast spread." The engine is built so that for a
future **live** event you'd swap the sampler for real GloFAS ensemble members with
no change to the aggregation — the seam exists, unimplemented. See
`UNCERTAINTY.md`.

### What is the robustness reversal, and is it real?

Yes, and it's reproducible (`just demo-seed`, fixed seed). *Wide coverage* wins the
deterministic score (82.6 vs 71.6) but *Focused & resourced* has a higher
worst-plausible floor (p05 ~66 vs ~63). Robustness is measured on the downside
(5th percentile) precisely because averages hide fragility. The tool detects and
headlines the reversal automatically.

### How do you stop the LLM from hallucinating numbers?

Structurally, not by hoping. The generator receives a typed **facts object** — the
only thing it may state as fact. After generation, a **numeric-consistency guard**
extracts every number from the AI text and checks it against the facts (tolerant
of formatting/rounding, strict on value). Any section containing a number that
isn't traceable to the facts is **rejected and replaced by the deterministic
template**. So a fabricated figure cannot ship. The whole thing also works with
**no API key** (pure template), and no test ever calls a real LLM. The same guard
protects the after-action assessment. See `BRIEF.md`.

### What's real vs. synthetic, and why include synthetic at all?

Real: admin boundaries + population (COD-AB/PS), the 2017 flood extent (UNOSAT/NRC),
OSM shelters & roads, GloFAS discharge, DesInventar historical incidents. Synthetic
/ assumption: landslide susceptibility (placeholder until NBRO), road closures
(sample), shelter capacities (planning assumption — OSM records none), resource
posture (a user decision variable). We include them so the *product* is complete
and demonstrable, but each is **flagged in the UI and preserved through scoring,
the brief, and the after-action** — never presented as real. `data-report` /
`just data-report` prints the full real-vs-synthetic ledger.

### The after-action says the plan "failed" — did you run it in 2017?

No, and the UI is explicit about this everywhere. The recorded side is the **actual
historical impact** (DesInventar), the historical response baseline — **not** the
outcome of executing a Praxis playbook. It's a *predicted-vs-recorded* benchmark:
did the strategy's at-risk ranking point where impact actually occurred? On the
seed data the answer is a striking **no** (inverted, Spearman −0.5), which is
exactly the kind of blind spot the Learn stage exists to surface.

### Is the after-action insight cherry-picked?

No — it falls out of the real data. Colombo, the most populous/flood-exposed
district, recorded **0 deaths** in 2017; Ratnapura, ranked last by flood exposure,
recorded the **most (84)**, as a landslide-prone hill district. The composite
impact (normalised deaths 0.5 / houses 0.3 / affected 0.2, raw components shown)
and the Spearman correlation are documented and deterministic. See `AFTER_ACTION.md`.

### Localization — did you machine-translate and hope?

The **core operational surface and every honesty/provenance/epistemic label** are
translated into Sinhala and Tamil, with self-hosted Noto fonts so both scripts
render offline. Anything not translated falls back to English per-key (never blank
or garbled). **Database content** (district names, source names) stays
English/romanized and is labeled as such — we don't fake-translate data.

### Does it work offline / on a bad network?

The app is an installable PWA. A service worker precaches the app shell, code, and
fonts, and serves API GETs network-first with a cache fallback, so a
previously-loaded dashboard survives a dropped connection. An honest **offline
indicator** and stale-data banner appear — cached data is never shown as live. The
one honest limitation: third-party CARTO basemap tiles aren't guaranteed
cacheable, so the map may render without tiles offline (the data still does).

### What's next?

Real **NBRO** landslide zonation and **DMC** operational feeds (replacing the two
synthetic layers); a **live-event mode** streaming actual response outcomes into
the after-action (the sampler and outcome seams already exist); and calibrating the
uncertainty distributions against observed outcomes over multiple events.
