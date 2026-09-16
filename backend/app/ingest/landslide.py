"""Ingest landslide susceptibility zonation for Ratnapura.

NBRO (National Building Research Organisation) publishes the authoritative
landslide hazard zonation for Sri Lanka, but it is not openly downloadable (it
requires a formal request). Per the project's data-integrity rule this pipeline:

  1. Loads a real NBRO file if you place one at ``data/raw/nbro_landslide.*``
     (GeoJSON/GPKG/zipped SHP), flagged as real; OR
  2. Otherwise generates a CLEARLY-SYNTHETIC placeholder susceptibility layer
     for Ratnapura district, flagged ``is_synthetic=True`` with source
     ``synthetic``, so real and sample data are never confused.

See docs/DATA_SOURCES.md for the access caveat.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.sync_session import sync_engine, sync_session
from app.etl.geo import as_multipolygon, force_multipolygon_column, to_wgs84
from app.etl.http import CACHE_DIR
from app.etl.loading import replace_geo_by_source
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario

_log = get_logger("praxis.ingest.landslide")

_RATNAPURA_PCODE = "LK91"
_PROVIDED_CANDIDATES = ("nbro_landslide.geojson", "nbro_landslide.gpkg", "nbro_landslide.zip")


def _provided_file() -> Path | None:
    for name in _PROVIDED_CANDIDATES:
        path = CACHE_DIR / name
        if path.exists() and path.stat().st_size > 0:
            return path
    return None


def _load_real(path: Path) -> dict[str, int]:
    gdf = force_multipolygon_column(to_wgs84(gpd.read_file(path)))
    with sync_session() as session:
        require_scenario(session)
        source = upsert_data_source(
            session,
            key="nbro-landslide",
            name="NBRO landslide susceptibility zonation (provided file)",
            url="https://www.nbro.gov.lk/",
            license="NBRO — provided under request; verify terms",
            notes=f"Loaded from operator-provided file {path.name}.",
            is_synthetic=False,
        )
        source_id = source.id
    gdf = gdf.assign(
        scenario_id=None,
        layer_type="landslide_susceptibility",
        name="NBRO landslide susceptibility (Ratnapura)",
        severity_class=None,
        severity_label=None,
        description="Landslide susceptibility zonation from a provided NBRO file.",
        is_synthetic=False,
        source_id=source_id,
    )
    rows = replace_geo_by_source(
        gdf[
            [
                "scenario_id",
                "layer_type",
                "name",
                "severity_class",
                "severity_label",
                "description",
                "is_synthetic",
                "source_id",
                "geometry",
            ]
        ],
        table="hazard_layer",
        source_id=source_id,
    )
    return {"landslide_layers_real": rows}


def _generate_synthetic() -> dict[str, int]:
    """Build a clearly-labelled synthetic susceptibility layer for Ratnapura."""
    district = gpd.read_postgis(
        "SELECT geom FROM admin_region WHERE pcode = %(pcode)s",
        sync_engine,
        geom_col="geom",
        params={"pcode": _RATNAPURA_PCODE},
    )
    if district.empty:
        raise RuntimeError("Ratnapura admin region not loaded; run `ingest admin` first.")
    poly = district.geometry.union_all()
    center = poly.representative_point()

    # Three distance bands from the district's steep interior — a placeholder,
    # NOT a hazard model. Flagged synthetic so it is never mistaken for NBRO.
    high = poly.intersection(center.buffer(0.10))
    moderate = poly.intersection(center.buffer(0.20)).difference(high)
    low = poly.difference(center.buffer(0.20))
    bands = [
        (3, "high", high),
        (2, "moderate", moderate),
        (1, "low", low),
    ]

    with sync_session() as session:
        require_scenario(session)
        source = upsert_data_source(
            session,
            key="synthetic-landslide",
            name="SYNTHETIC landslide susceptibility (sample)",
            url=None,
            license="synthetic",
            notes=(
                "Clearly-labelled SAMPLE data — NOT NBRO. Placeholder distance bands so the "
                "landslide layer exists for the demo. Replace with a real NBRO file to load "
                "authentic zonation."
            ),
            is_synthetic=True,
        )
        source_id = source.id

    geoms = [as_multipolygon(g) for _, _, g in bands]
    gdf = gpd.GeoDataFrame(
        {
            "scenario_id": [None] * 3,
            "layer_type": ["landslide_susceptibility"] * 3,
            "name": [f"SYNTHETIC susceptibility — {label} (Ratnapura)" for _, label, _ in bands],
            "severity_class": [cls for cls, _, _ in bands],
            "severity_label": [label for _, label, _ in bands],
            "description": ["SAMPLE placeholder — not a real hazard model."] * 3,
            "is_synthetic": [True] * 3,
            "source_id": [source_id] * 3,
            "geometry": geoms,
        },
        geometry="geometry",
        crs="EPSG:4326",
    )
    gdf = gdf[gdf.geometry.notna()]
    rows = replace_geo_by_source(gdf, table="hazard_layer", source_id=source_id)
    return {"landslide_layers_synthetic": rows}


def run_landslide() -> dict[str, int]:
    """Load real NBRO zonation if provided, else a flagged synthetic sample."""
    # Drop any previous susceptibility rows so switching real↔synthetic cannot
    # leave both sources visible at once.
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM hazard_layer
                WHERE layer_type = 'landslide_susceptibility'
                  AND source_id IN (
                      SELECT id FROM data_source
                      WHERE key IN ('synthetic-landslide', 'nbro-landslide')
                  )
                """
            )
        )
    provided = _provided_file()
    if provided is not None:
        _log.info("landslide.using_provided", file=provided.name)
        return _load_real(provided)
    _log.info("landslide.using_synthetic")
    return _generate_synthetic()
