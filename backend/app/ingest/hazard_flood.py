"""Ingest the real 2017 satellite flood extent as a scenario hazard layer.

Source: "Priority Index — Sri Lanka Floods May 2017" (Netherlands Red Cross,
CC BY, via HDX), whose ``flood_srilanka_new`` shapefile is a raster-derived
binary flood mask (~329k polygons nationwide). We clip it to the scenario
bounding box, dissolve to a single extent, and simplify for a usable payload.
"""

from __future__ import annotations

import geopandas as gpd
from shapely import make_valid
from shapely.geometry import MultiPolygon

from app.core.logging import get_logger
from app.db.sync_session import sync_session
from app.etl.geo import as_multipolygon, to_wgs84
from app.etl.hdx import get_dataset
from app.etl.http import download_file
from app.etl.loading import replace_geo_by_source
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario

_log = get_logger("praxis.ingest.hazard_flood")

DATASET = "priority-index-sri-lanka-floods-may-2017"
_SIMPLIFY_TOLERANCE_DEG = 0.0005  # ~50 m
_CLOSE_BUFFER_DEG = 0.0018  # ~200 m morphological close to merge raster cells
_MIN_PART_AREA_DEG2 = 2e-6  # drop isolated slivers below ~2.5 ha


def run_hazard_flood(*, force: bool = False) -> dict[str, int]:
    """Load the dissolved 2017 flood extent for the seed scenario. Idempotent."""
    with sync_session() as session:
        scenario = require_scenario(session)
        scenario_id = scenario.id
        bbox = (
            scenario.bbox_min_lon,
            scenario.bbox_min_lat,
            scenario.bbox_max_lon,
            scenario.bbox_max_lat,
        )

    ds = get_dataset(DATASET)
    res = ds.find(name_contains="flood_srilanka_new", fmt="SHP")
    zip_path = download_file(res.url, "flood_srilanka_new.zip", force=force)

    _log.info("hazard_flood.reading", bbox=bbox)
    gdf = gpd.read_file(f"/vsizip/{zip_path}/flood_new.shp", bbox=bbox)
    if gdf.empty:
        raise RuntimeError("Flood extent clip returned no polygons for the scenario bbox")
    gdf = to_wgs84(gdf)

    _log.info("hazard_flood.dissolving", polygons=len(gdf))
    dissolved = gdf.geometry.union_all()
    # Morphologically close the raster-derived mask so adjacent flooded cells
    # merge into contiguous inundation areas, then simplify for display.
    closed = dissolved.buffer(_CLOSE_BUFFER_DEG).buffer(-_CLOSE_BUFFER_DEG * 0.85)
    closed = make_valid(closed).simplify(_SIMPLIFY_TOLERANCE_DEG, preserve_topology=True)
    multi = as_multipolygon(closed)
    if multi is None:
        raise RuntimeError("Dissolved flood extent is not polygonal")
    # Drop isolated slivers (single-pixel noise) to keep the layer legible.
    parts = [g for g in multi.geoms if g.area >= _MIN_PART_AREA_DEG2]
    if parts:
        multi = MultiPolygon(parts)
    _log.info("hazard_flood.dissolved", parts=len(multi.geoms))

    with sync_session() as session:
        source = upsert_data_source(
            session,
            key="hdx-nrc-2017-flood-extent",
            name="Sri Lanka Floods May 2017 — flood extent (Netherlands Red Cross)",
            url=f"https://data.humdata.org/dataset/{DATASET}",
            license=ds.license,
            notes="Satellite-derived binary flood mask; clipped to scenario bbox and dissolved.",
        )
        source_id = source.id

    layer = gpd.GeoDataFrame(
        {
            "scenario_id": [scenario_id],
            "layer_type": ["flood_extent"],
            "name": ["2017 SW monsoon flood extent (Kalu Ganga basin)"],
            "severity_class": [None],
            "severity_label": ["inundated"],
            "description": ["Observed flood extent, May-June 2017 (dissolved, simplified)."],
            "is_synthetic": [False],
            "source_id": [source_id],
            "geometry": [multi],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )
    rows = replace_geo_by_source(layer, table="hazard_layer", source_id=source_id)
    return {"flood_extent_layers": rows, "source_polygons_clipped": len(gdf)}
