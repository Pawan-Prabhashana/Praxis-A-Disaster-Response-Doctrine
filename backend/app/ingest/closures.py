"""Derive scenario road closures from the observed flood extent.

No open real-time road-closure feed exists for Sri Lanka, so closures are
INFERRED: road segments intersecting the real 2017 flood extent are marked as
likely impassable. These are flagged ``is_synthetic=True`` (an inference, not an
official closure record) with source ``synthetic``.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logging import get_logger
from app.db.sync_session import sync_engine, sync_session
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario

_log = get_logger("praxis.ingest.closures")


def run_closures() -> dict[str, int]:
    """Create synthetic road closures where roads meet the flood extent."""
    with sync_session() as session:
        scenario = require_scenario(session)
        scenario_id = scenario.id
        source = upsert_data_source(
            session,
            key="synthetic-closures",
            name="SYNTHETIC road closures (inferred from flood extent)",
            url=None,
            license="synthetic",
            notes=(
                "Inferred: road segments intersecting the observed 2017 flood extent, marked "
                "impassable. Not an official closure record — flagged synthetic."
            ),
            is_synthetic=True,
        )
        source_id = source.id

    with sync_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM road_closure WHERE source_id = :sid AND scenario_id = :scid"),
            {"sid": source_id, "scid": scenario_id},
        )
        result = conn.execute(
            text(
                """
                INSERT INTO road_closure
                    (road_segment_id, scenario_id, reason, is_synthetic, source_id,
                     created_at, updated_at)
                SELECT rs.id, :scid,
                       'Intersects observed 2017 flood extent — likely impassable (inferred).',
                       true, :sid, now(), now()
                FROM road_segment rs
                JOIN hazard_layer hl
                  ON hl.layer_type = 'flood_extent' AND hl.scenario_id = :scid
                WHERE ST_Intersects(rs.geom, hl.geom)
                ON CONFLICT (road_segment_id, scenario_id) DO NOTHING
                """
            ),
            {"sid": source_id, "scid": scenario_id},
        )
    _log.info("closures.done", closures=result.rowcount)
    return {"road_closures": int(result.rowcount)}
