"""Unit tests for GeoJSON FeatureCollection helpers (pure Python, no PostGIS)."""

from __future__ import annotations

from app.api.geojson import collection, feature


def test_feature_and_collection_are_valid_geojson() -> None:
    feat = feature(
        id=1,
        geometry={"type": "Point", "coordinates": [80.384, 6.706]},
        properties={"name": "Ratnapura", "is_synthetic": False, "source": "test"},
    )
    fc = collection([feat])

    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["features"][0]["type"] == "Feature"
    assert fc["features"][0]["id"] == 1
    assert fc["features"][0]["geometry"]["type"] == "Point"
    assert fc["features"][0]["properties"]["is_synthetic"] is False


def test_empty_collection() -> None:
    fc = collection([])
    assert fc == {"type": "FeatureCollection", "features": []}


def test_feature_omits_id_when_absent() -> None:
    feat = feature(geometry=None, properties={})
    assert "id" not in feat
    assert feat["geometry"] is None
