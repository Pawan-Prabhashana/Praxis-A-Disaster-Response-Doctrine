# Praxis

**A Disaster Response Doctrine & Command Platform for Sri Lanka.**

Praxis is an authority-facing decision-support platform for Sri Lanka's disaster
management agencies — the Disaster Management Centre (DMC) and its district units.
It turns fragmented operational signals into deliberate action through a single,
continuous loop, and is built to feel like a calm, trustworthy command center
because it is used under stress.

> **Phase 2 — Data & geospatial core.** The platform now has a PostGIS domain
> model, repeatable ingestion of real public data, one seeded historical event
> (2017 SW-monsoon floods, Kalu Ganga basin), and GeoJSON read APIs. The Sense
> map arrives in Phase 3; stage routes still render designed placeholders.

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
