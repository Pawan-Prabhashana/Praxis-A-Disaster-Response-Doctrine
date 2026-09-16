"""The honesty dashboard: row counts per table with source and real/synthetic."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text

from app.db.sync_session import sync_engine

# Domain tables that carry a source_id (every ingested layer).
_TABLES = [
    "admin_region",
    "scenario",
    "hazard_layer",
    "incident",
    "shelter",
    "road_segment",
    "road_closure",
    "river_point",
    "discharge_forecast",
    "weather_reading",
]


@dataclass(frozen=True)
class ReportRow:
    """One (table, source) tally."""

    table: str
    source: str
    is_synthetic: bool
    rows: int


def build_report() -> list[ReportRow]:
    """Return per-table, per-source row counts joined to provenance."""
    out: list[ReportRow] = []
    with sync_engine.connect() as conn:
        for table in _TABLES:
            result = conn.execute(
                text(
                    f"""
                    SELECT ds.name AS source, ds.is_synthetic AS is_synthetic, COUNT(*) AS n
                    FROM {table} t
                    JOIN data_source ds ON ds.id = t.source_id
                    GROUP BY ds.name, ds.is_synthetic
                    ORDER BY n DESC
                    """
                )
            )
            for row in result:
                out.append(
                    ReportRow(
                        table=table,
                        source=row.source,
                        is_synthetic=bool(row.is_synthetic),
                        rows=int(row.n),
                    )
                )
    return out
