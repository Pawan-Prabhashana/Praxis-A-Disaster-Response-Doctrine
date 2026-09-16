"""Ingest daily weather for the basin over the event window (Open-Meteo)."""

from __future__ import annotations

from datetime import UTC, datetime, time

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.core.logging import get_logger
from app.db.sync_session import sync_session
from app.etl import seed_manifest as m
from app.etl.openmeteo import fetch_weather
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario
from app.models.weather import WeatherReading

_log = get_logger("praxis.ingest.weather")


def run_weather() -> dict[str, int]:
    """Fetch and store daily rainfall/temperature/wind for the event window."""
    with sync_session() as session:
        require_scenario(session)
        source = upsert_data_source(
            session,
            key="openmeteo-weather",
            name="Open-Meteo Weather API (ERA5 archive)",
            url="https://open-meteo.com/en/docs",
            license="Open-Meteo (CC BY 4.0); ERA5 / Copernicus Climate Change Service",
            notes="Daily precipitation, mean temperature, and max wind for the event window.",
        )
        source_id = source.id
        session.query(WeatherReading).filter_by(source_id=source_id).delete()
        session.flush()

        rows = 0
        for wp in m.WEATHER_POINTS:
            days = fetch_weather(wp.lat, wp.lon, m.EVENT_START, m.EVENT_END)
            geom = from_shape(Point(wp.lon, wp.lat), srid=4326)
            for day in days:
                session.add(
                    WeatherReading(
                        location_key=wp.key,
                        valid_time=datetime.combine(day.valid_date, time.min, tzinfo=UTC),
                        precipitation_mm=day.precipitation_mm,
                        temperature_c=day.temperature_c,
                        wind_speed_ms=day.wind_speed_ms,
                        source_id=source_id,
                        geom=geom,
                    )
                )
                rows += 1
            _log.info("weather.point_loaded", key=wp.key, days=len(days))

    return {"weather_readings": rows}
