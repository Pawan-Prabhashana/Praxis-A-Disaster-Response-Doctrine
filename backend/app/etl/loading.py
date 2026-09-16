"""Database write helpers for the ETL layer (sync engine).

Idempotency strategy: each layer is owned by its ``data_source``; a reload
deletes that source's existing rows and re-inserts, so re-running a pipeline is
always safe. Geometry is written with GeoPandas ``to_postgis`` (native WKB),
which is far simpler than hand-rolled bulk geometry inserts.
"""

from __future__ import annotations

import geopandas as gpd
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.sync_session import sync_engine

_log = get_logger("praxis.etl.loading")


def replace_geo_by_source(
    gdf: gpd.GeoDataFrame,
    *,
    table: str,
    source_id: int,
    geom_col: str = "geom",
) -> int:
    """Delete a source's rows in ``table`` and append ``gdf`` (idempotent reload).

    ``gdf`` must already be EPSG:4326 and carry every NOT NULL column the table
    requires (including ``source_id``). Returns the number of rows written.
    """
    if gdf.empty:
        raise ValueError(f"Refusing to load an empty GeoDataFrame into {table!r}")

    frame = gdf.rename_geometry(geom_col) if gdf.geometry.name != geom_col else gdf
    # Drop all-null attribute columns so pandas doesn't coerce integer NULLs to
    # float NaN (which PostgreSQL INTEGER columns reject).
    empty_cols = [
        col for col in frame.columns if col != frame.geometry.name and frame[col].isna().all()
    ]
    if empty_cols:
        frame = frame.drop(columns=empty_cols)

    with sync_engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table} WHERE source_id = :sid"), {"sid": source_id})

    # to_postgis manages its own connection; append after the delete is committed.
    frame.to_postgis(table, sync_engine, if_exists="append", index=False)
    _log.info("etl.loaded", table=table, rows=len(frame), source_id=source_id)
    return len(frame)


def delete_scenario_layer(table: str, *, source_id: int, scenario_id: int) -> None:
    """Delete rows for a given source+scenario (for scenario-scoped reloads)."""
    with sync_engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {table} WHERE source_id = :sid AND scenario_id = :scid"),
            {"sid": source_id, "scid": scenario_id},
        )
