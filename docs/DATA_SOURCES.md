# Praxis data sources

Every geospatial and tabular layer in Praxis is traced to a `data_source` row
(`name`, `url`, `license`, `fetched_at`, `notes`, `is_synthetic`). Real public
data and clearly-labelled sample data are never mixed without a flag. This
document is the human-readable ledger; `just data-report` is the live one.

## Seed event

**2017 South-West Monsoon Floods — Kalu Ganga basin**
(`slug`: `2017-sw-monsoon-kalu-ganga`).

- **Where.** Ratnapura (LK91) and Kalutara (LK13), plus neighbouring Galle,
  Matara, and Colombo districts.
- **When.** Peak around 26 May 2017 (ingest window 14 May – 3 June 2017).
- **Why this event.** The brief asked for the most recent SW-monsoon flood with
  a *genuinely downloadable* geospatial flood extent, centred on the Kalu Ganga
  basin. The 2024 SW-monsoon UNOSAT product
  ([unosat-live-web-map-floods-in-sri-lanka](https://data.humdata.org/dataset/unosat-live-web-map-floods-in-sri-lanka))
  is a live web map, not a clean vector download. The May 2017 event has a
  satellite-derived flood-extent shapefile on HDX (Netherlands Red Cross
  Priority Index dataset) that loads reproducibly. That is why 2017 was chosen
  over 2024.

## Real sources (ingested automatically)

| Source | URL | License (as recorded) | Feeds | Notes |
| ------ | --- | --------------------- | ----- | ----- |
| **HDX COD-AB** (OCHA) | https://data.humdata.org/dataset/cod-ab-lka | CKAN `license_title` at fetch time (typically CC BY) | `admin_region` levels 0–4 | GN divisions (level 4) scoped to the seed districts. Reprojected to EPSG:4326. |
| **HDX COD-PS** (OCHA) | https://data.humdata.org/dataset/cod-ps-lka | CKAN `license_title` at fetch time | `admin_region.population`, `name_si`/`name_ta` | 2023 population joined by P-code onto levels 0–2. |
| **HDX / Netherlands Red Cross — Sri Lanka Floods May 2017** | https://data.humdata.org/dataset/priority-index-sri-lanka-floods-may-2017 | CKAN `license_title` at fetch time (CC BY) | `hazard_layer` (`flood_extent`) | `flood_srilanka_new` shapefile, clipped to the scenario bbox, dissolved and simplified. Real observed extent, not a model. |
| **OpenStreetMap** via Overpass | https://www.openstreetmap.org/ | ODbL 1.0 | `shelter` (candidates), `road_segment` | Schools / community centres / colleges are **candidate** shelters, not an official DMC registry. Major roads only (motorway–secondary). |
| **Open-Meteo Flood API (GloFAS)** | https://open-meteo.com/en/docs/flood-api | Open-Meteo CC BY 4.0; GloFAS / Copernicus EMS | `river_point`, `discharge_forecast` | Ensemble daily discharge (m³/s). For *historical* dates GloFAS is a deterministic reanalysis — we store whatever the API returns and **do not synthesise** a spread. |
| **Open-Meteo Archive (ERA5)** | https://open-meteo.com/en/docs | Open-Meteo CC BY 4.0; ERA5 / C3S | `weather_reading` | Daily precip, mean temperature, max wind for the event window. |
| **DesInventar Sri Lanka** | https://www.desinventar.net/DesInventar/profiletab.jsp?countrycode=lka (export `DI_export_lka.zip`) | DesInventar / UNDRR terms | `incident` (historical) | Flood/landslide/storm cards in the seed districts, used as the Phase-7 Learn baseline. |
| **GDACS** | https://www.gdacs.org/ | JRC / UN OCHA public alerts | `incident` (`scenario_id` null) | Live regional alerts. Zero alerts is a valid outcome — never fabricated. |

Raw downloads land in `backend/data/raw/` (git-ignored). Re-runs reuse the cache
unless `--force` is passed.

## Sample / inferred data (flagged `is_synthetic = true`)

| Layer | Why it exists | How it is labelled |
| ----- | ------------- | ------------------- |
| **Road closures** | No open real-time closure feed for Sri Lanka. Segments intersecting the *real* 2017 flood extent are marked likely impassable. | `data_source.key = synthetic-closures`, `is_synthetic = true` on every row. |
| **Landslide susceptibility** | NBRO zonation is the authoritative product but is **not openly downloadable** (formal request). If you place a file at `backend/data/raw/nbro_landslide.{geojson,gpkg,zip}`, it is loaded as real. Otherwise a distance-band **placeholder** is generated for Ratnapura. | Synthetic rows: `data_source.key = synthetic-landslide`, names prefixed `SYNTHETIC`, `is_synthetic = true`. |

Shelter **capacity** is never invented. Candidate OSM facilities keep
`is_synthetic = false` (the geometry is real OSM) and a property note that they
are not an official registry.

## Access caveats (not downloadable without a request)

- **NBRO** (https://www.nbro.gov.lk) — landslide hazard zonation. Loader accepts
  an operator-provided file; otherwise a flagged sample is used.
- **DMC** (Disaster Management Centre) — official incident / shelter / situation
  reports are not published as open geospatial layers. Praxis does not scrape
  or fabricate them. OSM candidates and DesInventar history stand in until an
  official feed exists.

## Engine split

The API uses the **async** SQLAlchemy engine (`asyncpg`). Ingestion uses a
**separate sync** engine (`psycopg`) so GeoPandas `to_postgis` and bulk loads
stay simple. Both URLs are derived from the single `PRAXIS_DATABASE_URL`. See
`docs/ARCHITECTURE.md`.
