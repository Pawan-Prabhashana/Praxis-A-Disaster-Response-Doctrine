"""Geometry transform helpers (reprojection, type coercion, clipping)."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

WGS84 = "EPSG:4326"


def to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame to EPSG:4326, setting CRS if missing.

    COD-AB and most national datasets are already 4326, but flood/landslide
    sources can arrive in a local projection (e.g. Kandawala / SLD99), so every
    pipeline funnels geometry through here.
    """
    if gdf.crs is None:
        # A missing CRS on a national dataset is ambiguous; assume WGS84 only
        # when coordinates plausibly fall in lon/lat range, else fail loudly.
        bounds = gdf.total_bounds  # minx, miny, maxx, maxy
        if not (-180 <= bounds[0] <= 180 and -90 <= bounds[1] <= 90):
            raise ValueError(
                "GeoDataFrame has no CRS and coordinates are not lon/lat; "
                "cannot safely reproject."
            )
        return gdf.set_crs(WGS84)
    if gdf.crs.to_epsg() == 4326:
        return gdf
    return gdf.to_crs(WGS84)


def as_multipolygon(geom: BaseGeometry) -> MultiPolygon | None:
    """Coerce a (Multi)Polygon geometry to MultiPolygon; drop empties/others."""
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, MultiPolygon):
        return geom
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    if isinstance(geom, GeometryCollection):
        polys: list[Polygon] = []
        for part in geom.geoms:
            coerced = as_multipolygon(part)
            if coerced is not None:
                polys.extend(coerced.geoms)
        return MultiPolygon(polys) if polys else None
    return None


def force_multipolygon_column(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a copy whose geometry column is uniformly MultiPolygon (4326)."""
    out = gdf.copy()
    out["geometry"] = out["geometry"].apply(as_multipolygon)
    out = out[out["geometry"].notna()]
    return gpd.GeoDataFrame(out, geometry="geometry", crs=WGS84)
