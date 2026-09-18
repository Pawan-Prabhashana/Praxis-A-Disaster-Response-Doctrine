# Praxis

**A Disaster Response Doctrine & Command Platform for Sri Lanka.**

Praxis is an authority-facing decision-support platform for Sri Lanka's disaster
management agencies — the Disaster Management Centre (DMC) and its district units.
It turns fragmented operational signals into deliberate action through a single,
continuous loop, and is built to feel like a calm, trustworthy command center
because it is used under stress.

> **Phase 7 — Learn: the after-action review.** The Sense → Decide → Act → Learn
> loop is now complete. `/learn` compares a strategy's **predicted** at-risk ranking
> against the **actual recorded impact** of the real 2017 event (DesInventar) — an
> honest *predicted-vs-recorded* benchmark, never a claim the plan was executed. On
> the seed data the rankings are **inverted** (Spearman ≈ −0.5): Colombo, ranked
> most at-risk, recorded zero 2017 deaths, while Ratnapura, ranked last, recorded
> the most — the loop-closing lesson. See [`docs/AFTER_ACTION.md`](docs/AFTER_ACTION.md).

## The response loop

Praxis is organised around four stages that form a closed doctrine loop:

```
        ┌─────────────────────────────────────────────────────────────┐
        │                                                             │
        ▼                                                             │
  ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐ │
  │  01 SENSE │ ──▶ │ 02 DECIDE │ ──▶ │  03 ACT   │ ──▶ │ 04 LEARN  │─┘
  └───────────┘     └───────────┘     └───────────┘     └───────────┘
   Live picture      Playbook Studio    Operational       After-action
   of the event      — design, compare, brief ready to    review vs. the
   (incidents,       stress-test        execute in the    real outcome,
   shelters,         response           field.            feeding doctrine
   assets, roads).   strategies.                          back into Sense.
```

- **Sense** — a live operational dashboard: incidents, shelters, assets, road
  closures, and a map-backed situational picture.
- **Decide** — *Playbook Studio*, the flagship: design response strategies,
  compare them side by side, and stress-test each under uncertainty.
- **Act** — export a clear, ready-to-execute operational brief.
- **Learn** — compare the chosen plan against what actually happened.

## Tech stack

| Layer        | Choices                                                                                                   |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| **Frontend** | React 18 + TypeScript (strict), Vite, Tailwind CSS + shadcn/ui (Radix), MapLibre GL, TanStack Query, Zustand, Recharts, Framer Motion, i18next, Vitest, Biome |
| **Backend**  | Python 3.12, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy 2.0 (async) + GeoAlchemy2, Alembic, structlog, uv, Ruff, Pytest |
| **Data**     | PostgreSQL 16 + PostGIS 3.4 (Docker Compose)                                                               |
| **Tooling**  | `just` command runner, `uv` for Python, Docker Compose for infra                                          |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the rationale behind each
choice, and [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for the data ledger.

## Prerequisites

- [Docker](https://www.docker.com/) (with the daemon running)
- [`uv`](https://docs.astral.sh/uv/) — Python package manager
- [Node.js](https://nodejs.org/) 20+ and npm
- [`just`](https://github.com/casey/just) — command runner (`brew install just`)

## Quick start (from a fresh clone)

```bash
# 1. Configure environment (safe local defaults are provided).
cp .env.example .env

# 2. Install backend + frontend dependencies.
just setup

# 3. Start the database, apply migrations, load the seed scenario.
just db-up
just migrate
just data-load

# 4. Run the API and web app together.
just dev
```

Then open:

- **Web app** — http://localhost:5173
- **API health** — http://localhost:8000/health
- **API docs (Swagger)** — http://localhost:8000/docs

The system-status indicator in the top bar reflects the live `/health` result;
when the API and database are both up it reads **API Online**.

> **Note on ports.** The database publishes host port **5433** by default (the
> container still uses 5432 internally) to avoid clashing with any Postgres
> already running on the conventional 5432. Change `POSTGRES_PORT` in `.env` if
> you prefer another port.

## Common commands

| Command            | What it does                                        |
| ------------------ | --------------------------------------------------- |
| `just setup`       | Install backend + frontend dependencies             |
| `just db-up`       | Start Postgres/PostGIS and wait until healthy       |
| `just db-down`     | Stop the database (data preserved)                  |
| `just migrate`     | Apply Alembic migrations                            |
| `just data-load`   | Ingest public data and seed the 2017 Kalu Ganga scenario |
| `just data-report` | Row counts per table with source + real/synthetic   |
| `just api`         | Run the FastAPI backend (reload)                    |
| `just web`         | Run the Vite dev server                             |
| `just dev`         | Run API + web together                              |
| `just test`        | Fast unit tests (Pytest + Vitest; no Docker)        |
| `just test-integration` | PostGIS integration tests (needs `db-up` + `migrate` + `data-load`) |
| `just lint`        | Ruff + Biome + `tsc` strict typecheck               |
| `just format`      | Auto-format with Ruff + Biome                       |
| `just build`       | Production frontend build                           |

Run `just` with no arguments to list every recipe.

## Sense — operational dashboard (Phase 3)

The `/sense` route turns the seeded data into a command-center dashboard:

- **Map** (MapLibre GL, free CARTO dark/light basemaps, no API token) fit to the
  scenario's bounding box, with seven toggleable layers: admin population
  choropleth, flood extent, landslide susceptibility, roads (with closures),
  candidate shelters (clustered), historical incidents, and river gauges.
- **Left panel** — layer legend with real-vs-sample swatches, live feature
  counts, admin level switch, and a data-provenance popover.
- **Right panel** — details for the selected feature; clicking a river gauge
  shows the **GloFAS ensemble discharge** chart (median line + p25–p75 band).
- **KPI strip** — districts, affected population, historical incidents,
  candidate shelters + capacity, and road km (with closed km marked sample).

**Honesty by design:** any layer or feature with `is_synthetic = true` (the
landslide sample, inferred road closures) renders with a dashed/translucent
treatment and a "sample" tag in the legend, KPIs, and popups, so sample data is
never mistaken for authoritative data.

Start it with `just dev` and open http://localhost:5173/sense (select the seeded
scenario in the top bar if it is not already active).

## Playbook Studio — strategy builder & comparison (Phase 4)

The `/decide` route lets an authority design and compare response strategies
("playbooks") for the selected scenario, scored on a transparent, deterministic
scorecard.

- **Builder** — pick priority regions (with population + at-risk shown), activate
  shelters within them, set resource posture (teams/boats), evacuation threshold,
  and road-access handling. A compact context map (flood extent + priority
  regions + activated shelters) and a **live scorecard** update as you edit.
- **Compare** — select 2–3 playbooks for a side-by-side scorecard with
  best-in-row highlighting, a comparative bar chart, and each strategy's
  **coverage gaps** (at-risk regions it does not prioritise).
- **Scored on real data, honestly.** Every metric is computed from real ingested
  data with a documented formula (see [`docs/SCORING.md`](docs/SCORING.md)) and
  tagged **real / sample / assumption** — synthetic inputs (road closures) and
  planning assumptions (shelter capacity, resource model) are always visible,
  never hidden. Scores are deterministic: same levers + scenario → same result.

New playbooks start from **data-driven defaults** (top at-risk districts and the
shelters within them). Open http://localhost:5173/decide with `just dev` running.

## Stress-test engine — playbooks under uncertainty (Phase 5)

The deterministic scorecard answers *"how good is this playbook against the best
point estimate?"*. The stress-test engine answers *"how good is it across the
situations we cannot rule out — and does it still hold on a bad day?"*.

- **Explained, editable uncertainty.** A seeded Monte Carlo perturbs five inputs
  (displacement rate, at-risk population, resource effectiveness, shelter capacity,
  road-closure severity) over **documented distributions**. Each is shown with its
  distribution, its plain-language basis, and an **honesty-class badge**
  (*estimation error* / *assumption* / *sample-derived*), and can be toggled off.
- **Confidence bands + robustness.** Results show the score distribution
  (histogram), the **median** and **p05–p95 band**, the **worst-plausible** floor
  (p05 — "at least this in ~95% of modeled conditions"), and the **probability of
  meeting a target** (default 60). The deterministic point score is kept separate
  and drawn alongside for reference.
- **Compare under uncertainty.** Compare mode ranks strategies by their robustness
  band, and **flags a reversal** when the point winner is not the robust winner.
- **Honest by construction.** The seed event is historical (no GloFAS ensemble), so
  every result is labeled **modeled (epistemic)** uncertainty — parameter
  perturbation, never presented as measured forecast spread. Runs are **fully
  reproducible**: the seed is stored with every run.

**Try the built-in reversal demo.** With `just dev` running, at `/decide` create
two playbooks:

| Playbook | Priority regions | Shelters | Teams / boats |
| -------- | ---------------- | -------: | ------------- |
| **Wide coverage** | Colombo, Kalutara, Gampaha, Ratnapura, Galle | ~320 | 260 / 0 |
| **Focused & resourced** | Colombo, Kalutara | ~320 | 260 / 0 |

Stress-test each (default config, any fixed seed) and open **Compare**. *Wide
coverage* wins the deterministic scorecard (point ≈ 83 vs ≈ 72) but has a **lower
worst-plausible floor** (p05 ≈ 62 vs ≈ 65): spreading the same resources across
more people is fragile when displacement or the at-risk estimate runs high.
*Focused & resourced* is the **robust winner** — and Compare says so.

Full model, parameter bases, and the robustness definition:
[`docs/UNCERTAINTY.md`](docs/UNCERTAINTY.md).

## Operational brief — the Act stage (Phase 6)

The `/act` route turns a saved playbook (and, optionally, a stress-test run) into a
professional **operational brief**: situation, recommended strategy, expected
performance (scorecard + robustness), tasking, coverage gaps & risks, and
assumptions/provenance — ready to hand to field teams.

- **The LLM narrates real data; it never invents it.** Every figure comes from the
  Phase-4 scorecard and Phase-5 stress result, assembled into a typed facts object
  that is the *only* thing the model may state as fact. After generation a
  **numeric-consistency guard** checks every number in the prose against those
  facts; any section with an unverifiable number is silently replaced by the
  deterministic template. **A hallucinated figure cannot ship.** (Judge-defense and
  full trust model: [`docs/BRIEF.md`](docs/BRIEF.md).)
- **Works with no AI.** With `PRAXIS_LLM_ENABLED=false` or no key, the brief is
  produced entirely from the deterministic template — the app, tests, and exports
  all work offline with zero errors. A quiet indicator shows whether narration was
  AI-structured or template-only.
- **Honest by construction.** Provenance badges (real / sample / assumption), the
  synthetic-data caution, and the modeled-(epistemic)-uncertainty framing all
  survive into the document.
- **Export.** Print-ready **HTML** and a real downloadable **PDF** (server-rendered;
  pure-Python, no native deps), each with a provenance/generation footer.

**Enable AI narration locally** (optional) by setting in `.env`:

```bash
PRAXIS_LLM_ENABLED=true
PRAXIS_LLM_API_KEY=sk-ant-...      # your Anthropic key; never commit it
PRAXIS_LLM_MODEL=claude-sonnet-5
```

Open http://localhost:5173/act with `just dev` running, pick a playbook, and
**Generate brief**.

## After-action review — the Learn stage (Phase 7)

`/learn` closes the loop: it compares a strategy's **predicted** performance
against the **actual recorded impact** of the real historical event.

- **Predicted vs. recorded — honestly framed.** The recorded side is real
  DesInventar 2017 impact (deaths, people affected, houses destroyed) — the
  historical response baseline, **not** the outcome of executing the plan. Praxis
  was not running in 2017; the review says so everywhere.
- **Composite impact + alignment.** Districts are ranked by a documented composite
  (normalised deaths 0.5 / houses 0.3 / affected 0.2, raw components shown), and
  the predicted at-risk ranking is compared to the recorded impact ranking via a
  **Spearman correlation** and top-3 overlap, in plain language.
- **Blind spots & lessons.** High-impact districts the strategy under-prioritised
  or missed, plus structured lessons — every number traceable to real data.
  Recorded-impact map (choropleth), a predicted-vs-recorded rank scatter, and a
  "for next time" takeaway.
- **No fabricated outcomes.** Districts with no recorded data say "no recorded
  data." Lessons work with no LLM key (template); the optional narrated assessment
  passes the same numeric guard as the brief.

**The loop-closing insight (real seed data).** On the 2017 event the predicted and
recorded rankings are **inverted** (Spearman ≈ −0.5): Praxis ranks **Colombo** most
at-risk (largest flood-∩-population), yet Colombo recorded **0 deaths** in 2017,
while **Ratnapura** — ranked *last* at-risk — recorded the **most deaths (84)** as a
landslide-prone hill district. Lesson: weight recorded-impact history and landslide
susceptibility, not flood-inundation exposure alone.

Open http://localhost:5173/learn, pick a playbook, and **Run after-action**. Full
model: [`docs/AFTER_ACTION.md`](docs/AFTER_ACTION.md).

## Repository layout

```
Praxis/
├── backend/        FastAPI service (app/, migrations/, tests/)
├── frontend/       React app (src/app, routes, components/ui, lib, styles)
├── docs/           Architecture and design docs
├── docker-compose.yml
├── justfile
└── .env.example
```

## License

[MIT](LICENSE).
