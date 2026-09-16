"""Ingest OSM candidate shelters and the road network via Overpass."""

from __future__ import annotations

import json

import geopandas as gpd
from shapely.geometry import LineString, Point
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.sync_session import sync_engine, sync_session
from app.etl.http import CACHE_DIR
from app.etl.loading import replace_geo_by_source
from app.etl.overpass import (
    BBox,
    amenity_query,
    highway_query,
    parse_amenities,
    parse_highways,
    run_query,
)
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario

_log = get_logger("praxis.ingest.osm")

SHELTER_AMENITIES = ["school", "community_centre", "college"]
ROAD_CLASSES = ["motorway", "trunk", "primary", "secondary"]


def _cached_query(cache_name: str, query: str, *, force: bool) -> dict:
    path = CACHE_DIR / cache_name
    if path.exists() and path.stat().st_size > 0 and not force:
        _log.info("etl.cache_hit", filename=cache_name)
        return json.loads(path.read_text())
    payload = run_query(query)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return payload


def run_osm(*, force: bool = False) -> dict[str, int]:
    """Load candidate shelters and roads within the scenario bbox. Idempotent."""
    with sync_session() as session:
        scenario = require_scenario(session)
        bbox = BBox(
            south=scenario.bbox_min_lat,
            west=scenario.bbox_min_lon,
            north=scenario.bbox_max_lat,
            east=scenario.bbox_max_lon,
        )
        shelter_source = upsert_data_source(
            session,
            key="osm-shelters",
            name="OpenStreetMap — candidate shelters (schools, community centres)",
            url="https://www.openstreetmap.org/",
            license="ODbL 1.0",
            notes="CANDIDATE shelters derived from OSM facilities — not an official registry.",
        )
        road_source = upsert_data_source(
            session,
            key="osm-roads",
            name="OpenStreetMap — road network",
            url="https://www.openstreetmap.org/",
            license="ODbL 1.0",
            notes="Major roads (motorway/trunk/primary/secondary) within the scenario bbox.",
        )
        shelter_source_id, road_source_id = shelter_source.id, road_source.id

    # --- Shelters ---------------------------------------------------------
    shelter_payload = _cached_query(
        "overpass_shelters.json", amenity_query(bbox, SHELTER_AMENITIES), force=force
    )
    amenities = parse_amenities(shelter_payload)
    shelters = gpd.GeoDataFrame(
        {
            "osm_id": [a["osm_id"] for a in amenities],
            "name": [a["name"] or f"Unnamed {a['kind'].replace('_', ' ')}" for a in amenities],
            "kind": [a["kind"] for a in amenities],
            "capacity": [None] * len(amenities),
            "admin_region_id": [None] * len(amenities),
            "source_id": [shelter_source_id] * len(amenities),
            "is_synthetic": [False] * len(amenities),
            "geometry": [Point(a["lon"], a["lat"]) for a in amenities],
        },
        geometry="geometry",
        crs="EPSG:4326",
    ).drop_duplicates(subset="osm_id")
    shelter_rows = replace_geo_by_source(shelters, table="shelter", source_id=shelter_source_id)

    # --- Roads ------------------------------------------------------------
    road_payload = _cached_query(
        "overpass_roads.json", highway_query(bbox, ROAD_CLASSES), force=force
    )
    highways = parse_highways(road_payload)
    roads = gpd.GeoDataFrame(
        {
            "osm_id": [h["osm_id"] for h in highways],
            "road_class": [h["road_class"] for h in highways],
            "name": [h["name"] for h in highways],
            "source_id": [road_source_id] * len(highways),
            "geometry": [LineString(h["coords"]) for h in highways],
        },
        geometry="geometry",
        crs="EPSG:4326",
    ).drop_duplicates(subset="osm_id")
    road_rows = replace_geo_by_source(roads, table="road_segment", source_id=road_source_id)

    # Link shelters to their DS division (admin level 3) by point-in-polygon.
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE shelter s
                SET admin_region_id = a.id
                FROM admin_region a
                WHERE a.level = 3
                  AND s.source_id = :sid
                  AND ST_Contains(a.geom, s.geom)
                """
            ),
            {"sid": shelter_source_id},
        )

    return {"shelters": shelter_rows, "roads": road_rows}
