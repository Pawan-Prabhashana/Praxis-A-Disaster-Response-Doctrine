"""Ingest GloFAS river-discharge for the seed river points (Open-Meteo Flood API)."""

from __future__ import annotations

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.core.logging import get_logger
from app.db.sync_session import sync_session
from app.etl import seed_manifest as m
from app.etl.openmeteo import fetch_discharge
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario
from app.models.river import DischargeForecast, RiverPoint

_log = get_logger("praxis.ingest.flood")


def run_discharge() -> dict[str, int]:
    """Fetch and store ensemble river discharge for the event window. Idempotent."""
    with sync_session() as session:
        scenario = require_scenario(session)
        scenario_id = scenario.id
        source = upsert_data_source(
            session,
            key="openmeteo-glofas",
            name="Open-Meteo Flood API (GloFAS river discharge)",
            url="https://open-meteo.com/en/docs/flood-api",
            license="Open-Meteo (CC BY 4.0); GloFAS / Copernicus Emergency Management Service",
            notes=(
                "Ensemble daily river discharge (m³/s). For historical dates GloFAS is a "
                "deterministic reanalysis, so percentile fields equal the deterministic value."
            ),
        )
        source_id = source.id

        # Idempotent reload: discharge rows first (FK), then river points.
        session.query(DischargeForecast).filter_by(source_id=source_id).delete()
        session.query(RiverPoint).filter_by(source_id=source_id).delete()
        session.flush()

        point_count = 0
        forecast_count = 0
        for rp in m.RIVER_POINTS:
            days, grid_lat, grid_lon = fetch_discharge(rp.lat, rp.lon, m.EVENT_START, m.EVENT_END)
            river_point = RiverPoint(
                key=rp.key,
                name=rp.name,
                river_name=rp.river_name,
                source_id=source_id,
                geom=from_shape(Point(grid_lon, grid_lat), srid=4326),
            )
            session.add(river_point)
            session.flush()
            point_count += 1

            for day in days:
                session.add(
                    DischargeForecast(
                        river_point_id=river_point.id,
                        scenario_id=scenario_id,
                        issued_at=None,  # reanalysis, not a forecast issuance
                        valid_date=day.valid_date,
                        discharge_mean=day.mean,
                        discharge_median=day.median,
                        discharge_p25=day.p25,
                        discharge_p75=day.p75,
                        discharge_min=day.minimum,
                        discharge_max=day.maximum,
                        source_id=source_id,
                    )
                )
                forecast_count += 1
            _log.info("flood.point_loaded", key=rp.key, days=len(days))

    return {"river_points": point_count, "discharge_forecasts": forecast_count}
