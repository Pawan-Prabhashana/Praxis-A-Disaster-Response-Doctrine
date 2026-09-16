# Praxis — Architecture

This document explains how Praxis is structured, why each technology was chosen,
and which external data sources will feed the platform in later phases. It is the
reference for reviewers and future contributors.

## 1. The operating model: Sense → Decide → Act → Learn

Praxis is deliberately organised as a **doctrine loop** rather than a set of
disconnected screens. Emergency management is cyclical: authorities build a
picture, choose a course of action, execute it, and learn from the result — then
do it again as the situation evolves. The product mirrors that cycle exactly.

| Stage      | Question it answers                     | What lives here (from Phase 2 on)                                                            |
| ---------- | --------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Sense**  | *What is happening right now?*           | Live dashboard: incidents, shelters, assets, road closures, and a MapLibre situational map. |
| **Decide** | *What should we do about it?*            | **Playbook Studio** (flagship): compose response strategies, compare them, stress-test under uncertainty. |
| **Act**    | *How do we execute the chosen plan?*     | Export a ready-to-execute operational brief (tasks, assignments, timing).                   |
| **Learn**  | *Did it work, and what do we change?*    | After-action comparison of the chosen plan vs. the actual outcome; feeds doctrine back into Sense. |

**Design consequence.** The frontend's primary navigation *is* the loop
(`/sense`, `/decide`, `/act`, `/learn`), with an overview landing at `/`. The
sidebar renders the four stages as an ordered, visually connected sequence so the
cycle is legible at a glance. This model is encoded once in
`frontend/src/config/nav.ts` and shared by the sidebar, routes, and landing page.

## 2. System shape

```
┌──────────────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│        Frontend          │  ───────────────────▶   │         Backend          │
│  React + Vite (SPA)      │                         │  FastAPI (async)         │
│  TanStack Query · Zustand│  ◀───────────────────   │  Pydantic v2 · structlog │
│  Tailwind + shadcn/ui    │        /health          │  request-id middleware   │
│  MapLibre GL (Phase 2)   │        /api/v1/*        │                          │
└──────────────────────────┘                         └────────────┬─────────────┘
                                                                   │ SQLAlchemy 2.0 (async)
                                                                   │ + GeoAlchemy2
                                                                   ▼
                                                     ┌──────────────────────────┐
                                                     │   PostgreSQL 16 + PostGIS │
                                                     │   (Docker Compose)        │
                                                     └──────────────────────────┘
```

- The **frontend** is a single-page app. Server state (health, and later
  incidents/scenarios) is owned by **TanStack Query**; ephemeral UI state (theme,
  sidebar) by **Zustand**. This separation keeps caching/refetching concerns out
  of component-local state.
- The **backend** is an async FastAPI app. `/health` performs a real database
  probe; `/api/v1/*` is the versioned domain surface. A request-id middleware
  binds a correlation id onto every structured log line.
- **PostGIS** is the spatial backbone. Phase 1 only enables the extension; domain
  tables (with geometry/geography columns) arrive in Phase 2.

## 3. Stack decisions — and why

### Frontend

- **React 18 + TypeScript (strict).** Strict mode (`noImplicitAny`,
  `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, …) catches whole
  classes of defects before runtime — appropriate for a public-safety tool.
- **Vite.** Near-instant dev server and fast, modern production builds; the
  default for new React apps.
- **Tailwind CSS + shadcn/ui (Radix).** Tailwind gives a constrained, token-driven
  styling system; shadcn/Radix supply accessible, unstyled primitives we own and
  restyle. Components live *in the repo* (not a black-box library), so the design
  system is fully under our control. The tokens are defined once in
  `src/styles/globals.css` and bridged through `tailwind.config.ts`.
- **MapLibre GL JS.** Open-source, no API token, works with free vector basemaps
  (e.g. OpenFreeMap) — important for a public-sector tool with no vendor lock-in.
  Wired into Sense in Phase 2.
- **TanStack Query + Zustand.** Best-in-class server-state caching and a tiny,
  ergonomic client-state store, respectively.
- **Framer Motion / lucide-react.** Restrained motion for a calm feel and a
  consistent icon set (both used from Phase 1). **Recharts** (charts for
  Decide/Learn) and **MapLibre GL** (the Sense map) are part of the stack but are
  introduced when their stages gain data in Phase 2 — they are intentionally not
  pulled in as unused dependencies now.
- **i18next.** Localisation scaffolding is in place with English wired now;
  Sinhala (`si`) and Tamil (`ta`) — Sri Lanka's other official languages — slot in
  during Phase 8 with no structural change.
- **Vitest + Testing Library.** Fast, Vite-native testing.
- **Biome.** A single fast tool for both lint and format, replacing the
  ESLint + Prettier pair to reduce config surface and CI time.

### Backend

- **Python 3.12 + FastAPI + Pydantic v2.** Async-first, type-driven APIs with
  automatic OpenAPI docs. Pydantic v2 gives fast validation and clean schema
  definitions shared with the frontend's TypeScript types.
- **SQLAlchemy 2.0 (async) + GeoAlchemy2.** The 2.0 typed ORM with async engines
  (via `asyncpg`); GeoAlchemy2 adds PostGIS geometry types for the spatial domain.
- **Alembic (async).** Schema migrations run against the same async engine and
  metadata the app uses, so there is one source of truth. The initial migration
  enables PostGIS and creates no domain tables yet.
- **pydantic-settings.** Environment-driven config with typed defaults; a fresh
  clone boots without manual setup.
- **structlog.** Structured (JSON in production) logs with a per-request id for
  correlation.
- **uv.** Fast, reproducible Python dependency management and virtual envs.
- **Ruff.** A single fast tool for lint + format on the Python side (mirrors
  Biome's role on the frontend).

### Data / infra

- **PostgreSQL 16 + PostGIS 3.4 via Docker Compose.** A reproducible local spatial
  database with a persisted named volume. The host port defaults to **5433** to
  avoid clashing with a stock local Postgres.

## 4. Configuration & security posture

- All configuration is environment-driven (`.env`, documented in `.env.example`).
  The real `.env` is git-ignored; only defaults safe for local development are
  committed.
- CORS is restricted to the configured frontend origin(s).
- Accessibility and contrast are treated as first-class: the theme targets WCAG AA
  because operators use this under stress, often on imperfect displays.

## 5. Planned public data sources (Phase 2+)

Praxis is designed to integrate authoritative, mostly-open data. These are noted
now so the schema and ingestion design can anticipate them; **no ingestion is
implemented in Phase 1.**

| Source                          | Role in Praxis                                                        |
| ------------------------------- | -------------------------------------------------------------------- |
| **Open-Meteo**                  | Weather + precipitation forecasts driving hazard context (Sense).    |
| **GloFAS** (Global Flood Awareness System) | Riverine flood forecasting and reanalysis.                |
| **HDX** (Humanitarian Data Exchange) | Administrative boundaries and population baselines for Sri Lanka. |
| **OpenStreetMap**               | Roads, facilities, and basemap features (also MapLibre tiles).       |
| **NBRO** (National Building Research Organisation) | Landslide hazard zonation for Sri Lanka.          |
| **DesInventar**                 | Historical disaster loss database for baselines and Learn.           |
| **UNOSAT**                      | Satellite-derived flood/damage extents during events.                |
| **GDACS** (Global Disaster Alert and Coordination System) | Global multi-hazard alerts and impact estimates. |
| **DMC** (Disaster Management Centre, Sri Lanka) | Authoritative national incident, shelter, and situation reports. |

Each source will be adapted behind a normalised internal model so the loop is
agnostic to any single provider's availability or format.

## 6. Phase roadmap (abridged)

- **Phase 1 (this repo).** Foundation: shell, design system, API skeleton, DB +
  migrations, local dev environment.
- **Phase 2.** Domain models + spatial schema; Sense dashboard and MapLibre layers;
  first data-source integrations.
- **Later.** Playbook Studio (Decide), operational brief export (Act), after-action
  review (Learn), and full Sinhala/Tamil localisation (Phase 8).
