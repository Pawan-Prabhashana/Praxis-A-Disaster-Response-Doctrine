# Praxis Backend

FastAPI service for **Praxis — Disaster Response Doctrine & Command Platform**.

- **Runtime:** Python 3.12, FastAPI, Uvicorn
- **Data:** SQLAlchemy 2.0 (async, `asyncpg`) + GeoAlchemy2 on PostgreSQL 16 / PostGIS 3.4
- **Migrations:** Alembic (async)
- **Config:** pydantic-settings (`PRAXIS_*` env vars) · **Logging:** structlog

See the repository root `README.md` for full setup, and `docs/ARCHITECTURE.md`
for the design rationale. Common tasks are exposed through the root `justfile`.

## Endpoints

| Method | Path            | Purpose                                          |
| ------ | --------------- | ------------------------------------------------ |
| `GET`  | `/health`       | Liveness + live database connectivity probe      |
| `GET`  | `/api/v1/meta`  | App name, version, and scenario catalogue (stub) |
| `GET`  | `/docs`         | Interactive OpenAPI (Swagger UI)                 |
