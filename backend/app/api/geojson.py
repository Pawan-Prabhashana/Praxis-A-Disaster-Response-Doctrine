"""Helper to build GeoJSON FeatureCollections in PostGIS.

Letting the database assemble GeoJSON (``ST_AsGeoJSON`` +
``jsonb_build_object``) is both correct and fast, and keeps geometry handling
out of Python. Each endpoint supplies an inner SELECT that yields one ``feature``
(jsonb) per row; this wraps them into a FeatureCollection.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def feature(
    *,
    geometry: dict[str, Any] | None,
    properties: dict[str, Any],
    id: int | str | None = None,
) -> dict[str, Any]:
    """Build a single GeoJSON Feature (pure Python; used by tests and helpers)."""
    feat: dict[str, Any] = {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties,
    }
    if id is not None:
        feat["id"] = id
    return feat


def collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap Feature dicts in a GeoJSON FeatureCollection."""
    return {"type": "FeatureCollection", "features": features}


async def feature_collection(
    session: AsyncSession, inner_sql: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute an inner SELECT (yielding a ``feature`` column) as a FeatureCollection."""
    stmt = text(
        f"""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(f.feature), '[]'::jsonb)
        )
        FROM ({inner_sql}) AS f
        """
    )
    result = await session.execute(stmt, params)
    return result.scalar_one()
