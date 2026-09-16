"""Unit tests for Overpass QL builders and payload parsers."""

from __future__ import annotations

from app.etl.overpass import BBox, amenity_query, parse_amenities, parse_highways


def test_bbox_overpass_order() -> None:
    bbox = BBox(south=6.4, west=79.8, north=6.9, east=80.6)
    assert bbox.as_overpass() == "6.4,79.8,6.9,80.6"


def test_amenity_query_includes_kinds_and_bbox() -> None:
    q = amenity_query(BBox(6.4, 79.8, 6.9, 80.6), ["school", "community_centre"])
    assert 'node["amenity"="school"]' in q
    assert 'way["amenity"="community_centre"]' in q
    assert "6.4,79.8,6.9,80.6" in q
    assert "out center tags" in q


def test_parse_amenities_nodes_and_way_centroids() -> None:
    payload = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 6.7,
                "lon": 80.4,
                "tags": {"amenity": "school", "name": "St. Luke's"},
            },
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 6.71, "lon": 80.41},
                "tags": {"amenity": "community_centre"},
            },
            {"type": "way", "id": 3, "tags": {"amenity": "school"}},  # no centre → skip
        ]
    }
    rows = parse_amenities(payload)
    assert len(rows) == 2
    assert rows[0]["osm_id"] == "node/1"
    assert rows[0]["name"] == "St. Luke's"
    assert rows[1]["kind"] == "community_centre"
    assert rows[1]["lat"] == 6.71


def test_parse_highways_requires_two_vertices() -> None:
    payload = {
        "elements": [
            {
                "type": "way",
                "id": 10,
                "tags": {"highway": "primary", "name": "Colombo Rd"},
                "geometry": [
                    {"lon": 80.0, "lat": 6.5},
                    {"lon": 80.1, "lat": 6.51},
                ],
            },
            {
                "type": "way",
                "id": 11,
                "tags": {"highway": "primary"},
                "geometry": [{"lon": 80.0, "lat": 6.5}],
            },
        ]
    }
    rows = parse_highways(payload)
    assert len(rows) == 1
    assert rows[0]["osm_id"] == "way/10"
    assert rows[0]["coords"] == [(80.0, 6.5), (80.1, 6.51)]
