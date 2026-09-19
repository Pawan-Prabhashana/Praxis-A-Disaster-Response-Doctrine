# Deployment

Praxis ships as three containers — **db** (PostgreSQL/PostGIS), **api** (FastAPI),
and **web** (the built SPA served by nginx, which also proxies `/api`). Everything
is env-driven; no secrets are committed.

## Prerequisites

- Docker + Docker Compose
- (For loading seed data) network access to the public data sources

## 1. Clone and configure

```bash
git clone https://github.com/Pawan-Prabhashana/Praxis-A-Disaster-Response-Doctrine.git
cd Praxis-A-Disaster-Response-Doctrine
cp .env.prod.example .env.prod
# Edit .env.prod — set a real POSTGRES_PASSWORD at minimum.
```

## 2. Build and start the stack

```bash
just prod-up            # docker compose -p praxis-prod -f docker-compose.prod.yml up -d --build
```

Or without `just`:

```bash
docker compose -p praxis-prod -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

What happens:

- **db** starts and becomes healthy.
- **api** waits for the db, then its entrypoint runs `alembic upgrade head`
  (idempotent) and starts uvicorn on port 8000. A healthcheck polls `/health`.
- **web** builds the Vite bundle (with an empty API base URL → same-origin
  relative `/api` requests) and serves it via nginx on the host `WEB_PORT`
  (default **8080**), proxying `/api` and `/health` to the api service.

Open **http://localhost:8080**. The system-status pill should read *API Online*
once the api is healthy.

## 3. Load the seed scenario (real public data)

A fresh database has the schema but no data. Load the 2017 Kalu Ganga seed
scenario (downloads real public data — COD-AB/PS, UNOSAT flood extent, OSM,
GloFAS, DesInventar; needs network and the ETL extra):

```bash
just prod-data-load
```

This runs the ETL CLI in a throwaway api container (installing the `etl` extra on
the fly). It is idempotent and cached. Then verify:

```bash
docker compose -p praxis-prod -f docker-compose.prod.yml --env-file .env.prod \
  run --rm --entrypoint "" api python -m app.cli data-report
```

## 4. Seed the demo showcase (optional but recommended)

Create the two showcase playbooks + fixed-seed stress runs so the robustness
reversal and the after-action inverted-alignment insight are reproducible:

```bash
just prod-demo-seed
```

## 5. Enable AI narration (optional)

The operational brief and after-action assessment work **without** an LLM (a
deterministic template). To enable AI-structured narration (still validated by
the numeric guard), set in `.env.prod` and restart the api:

```bash
PRAXIS_LLM_ENABLED=true
PRAXIS_LLM_API_KEY=sk-ant-...     # your Anthropic key — never commit it
PRAXIS_LLM_MODEL=claude-sonnet-5
```

```bash
docker compose -p praxis-prod -f docker-compose.prod.yml --env-file .env.prod up -d api
```

## Operations

```bash
just prod-logs     # tail all services
just prod-down     # stop (data volume praxis-prod-db-data is preserved)
```

To wipe the database volume: add `-v` to the down command.

## Configuration reference

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | praxis / *(change)* / praxis | Database credentials; also composed into the API's async URL. |
| `WEB_PORT` | 8080 | Host port for the web app. |
| `PRAXIS_CORS_ORIGINS` | http://localhost:8080 | Allowed browser origins (the app is same-origin, so this rarely matters). |
| `PRAXIS_LLM_ENABLED` | false | Turn on AI narration. |
| `PRAXIS_LLM_API_KEY` | *(empty)* | Anthropic key. Never committed. |
| `PRAXIS_LLM_MODEL` | claude-sonnet-5 | Model id. |

## Notes & honest limitations

- **Migrations** run automatically on api start (entrypoint). Rolling back is a
  manual `alembic downgrade` inside the api container.
- **Basemap tiles** come from CARTO (third-party). They are cached best-effort by
  the service worker but are **not guaranteed available offline** — the app shell
  and previously loaded data still work; the map may render without tiles.
- **The api image is lean** (no GeoPandas/GDAL). The `etl` extra is installed
  on-demand for `prod-data-load` only.
- **TLS / reverse proxy**: for a public deployment, terminate TLS at a proxy
  (Caddy/Traefik/ALB) in front of the web container and set `PRAXIS_CORS_ORIGINS`
  and the public origin accordingly.
