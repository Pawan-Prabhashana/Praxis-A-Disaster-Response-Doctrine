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
