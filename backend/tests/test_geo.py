"""Unit tests for reprojection / geometry helpers.

Requires the ETL extra (geopandas). Skipped if it is not installed so
``just test`` stays usable on an API-only venv.
"""

from __future__ import annotations

import pytest

gpd = pytest.importorskip("geopandas")
shapely = pytest.importorskip("shapely")

from shapely.geometry import GeometryCollection, Point, Polygon

from app.etl.geo import as_multipolygon, to_wgs84


def test_to_wgs84_reprojects_from_web_mercator() -> None:
    src = gpd.GeoDataFrame(geometry=[Point(80.4, 6.7)], crs="EPSG:4326").to_crs(3857)
    out = to_wgs84(src)
    assert out.crs.to_epsg() == 4326
    lon, lat = out.geometry.iloc[0].x, out.geometry.iloc[0].y
    assert lon == pytest.approx(80.4, abs=1e-5)
    assert lat == pytest.approx(6.7, abs=1e-5)


def test_to_wgs84_sets_crs_when_coords_are_lonlat() -> None:
    gdf = gpd.GeoDataFrame(geometry=[Point(80.4, 6.7)], crs=None)
    out = to_wgs84(gdf)
    assert out.crs.to_epsg() == 4326


def test_to_wgs84_rejects_projected_coords_without_crs() -> None:
    gdf = gpd.GeoDataFrame(geometry=[Point(500_000, 200_000)], crs=None)
    with pytest.raises(ValueError, match="no CRS"):
        to_wgs84(gdf)


def test_as_multipolygon_coerces_polygon_and_collection() -> None:
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    multi = as_multipolygon(poly)
    assert multi is not None and multi.geom_type == "MultiPolygon"

    collected = as_multipolygon(GeometryCollection([poly]))
    assert collected is not None and len(collected.geoms) == 1

    assert as_multipolygon(Point(0, 0)) is None
