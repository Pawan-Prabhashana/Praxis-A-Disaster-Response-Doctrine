"""Ingest current GDACS alerts as scenario-independent reference incidents."""

from __future__ import annotations

from datetime import UTC, datetime, time

import geopandas as gpd
from shapely.geometry import Point

from app.core.logging import get_logger
from app.db.sync_session import sync_session
from app.etl.gdacs import fetch_alerts
from app.etl.loading import replace_geo_by_source
from app.etl.provenance import upsert_data_source

_log = get_logger("praxis.ingest.gdacs")

# South Asia / North Indian Ocean region (min_lon, min_lat, max_lon, max_lat).
SOUTH_ASIA_BBOX = (60.0, 0.0, 100.0, 35.0)


def run_gdacs() -> dict[str, int]:
    """Fetch current GDACS alerts in the region and store them as incidents.

    Zero alerts is a valid (documented) outcome — the feed is live. Alerts are
    real and scenario-independent (``scenario_id`` is null).
    """
    alerts = fetch_alerts(bbox=SOUTH_ASIA_BBOX)

    with sync_session() as session:
        source = upsert_data_source(
            session,
            key="gdacs-alerts",
            name="GDACS — Global Disaster Alert and Coordination System",
            url="https://www.gdacs.org/",
            license="GDACS (JRC/UN OCHA) — public alerts",
            notes="Current global alerts clipped to the South Asia region; live reference.",
        )
        source_id = source.id

    if not alerts:
        # Clear any stale rows and report zero — never fabricate.
        from sqlalchemy import text

        from app.db.sync_session import sync_engine

        with sync_engine.begin() as conn:
            conn.execute(text("DELETE FROM incident WHERE source_id = :sid"), {"sid": source_id})
        _log.info("gdacs.no_alerts_in_region")
        return {"gdacs_alerts": 0}

    gdf = gpd.GeoDataFrame(
        {
            "external_id": [a.external_id for a in alerts],
            "type": [f"gdacs:{a.event_type}" for a in alerts],
            "severity": [a.alert_level for a in alerts],
            "description": [f"{a.title} ({a.country or 'n/a'})" for a in alerts],
            "occurred_at": [
                datetime.combine(a.occurred_on, time.min, tzinfo=UTC) if a.occurred_on else None
                for a in alerts
            ],
            "admin_region_id": [None] * len(alerts),
            "scenario_id": [None] * len(alerts),
            "source_id": [source_id] * len(alerts),
            "is_synthetic": [False] * len(alerts),
            "geometry": [Point(a.lon, a.lat) for a in alerts],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )
    rows = replace_geo_by_source(gdf, table="incident", source_id=source_id)
    return {"gdacs_alerts": rows}
