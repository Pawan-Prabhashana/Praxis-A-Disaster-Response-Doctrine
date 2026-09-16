# Praxis Backend

FastAPI service for **Praxis — Disaster Response Doctrine & Command Platform**.

- **Runtime:** Python 3.12, FastAPI, Uvicorn
- **Data:** SQLAlchemy 2.0 (async, `asyncpg`) + GeoAlchemy2 on PostgreSQL 16 / PostGIS 3.4.
  ETL / the Typer CLI use a **separate sync** engine (`psycopg`) — see `app/db/sync_session.py`.
- **Migrations:** Alembic (async). 0001 enables PostGIS; 0002 is the domain model.
- **Config:** pydantic-settings (`PRAXIS_*` env vars) · **Logging:** structlog

See the repository root `README.md` for full setup, `docs/ARCHITECTURE.md`
for the design rationale, and `docs/DATA_SOURCES.md` for the data ledger.
Common tasks are exposed through the root `justfile`.

## CLI

```bash
uv run python -m app.cli ingest admin
uv run python -m app.cli seed-scenario
uv run python -m app.cli data-report
```

(`just data-load` / `just data-report` wrap the last two.)

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/health` | Liveness + live database connectivity probe |
| `GET` | `/api/v1/meta` | App name, version |
| `GET` | `/api/v1/scenarios` | Scenario list (selector) |
| `GET` | `/api/v1/scenarios/{slug}` | Detail, bbox/center, layer counts, provenance |
| `GET` | `/api/v1/scenarios/{slug}/admin-regions?level=` | GeoJSON (simplified) |
| `GET` | `/api/v1/scenarios/{slug}/hazard-layers?type=` | GeoJSON |
| `GET` | `/api/v1/scenarios/{slug}/shelters` | GeoJSON (OSM candidates) |
| `GET` | `/api/v1/scenarios/{slug}/incidents` | GeoJSON |
| `GET` | `/api/v1/scenarios/{slug}/roads?closed=` | GeoJSON |
| `GET` | `/api/v1/scenarios/{slug}/rivers` | GeoJSON |
| `GET` | `/api/v1/scenarios/{slug}/discharge?river_point_id=` | Ensemble discharge JSON |
| `GET` | `/docs` | Interactive OpenAPI (Swagger UI) |
