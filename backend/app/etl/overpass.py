"""OpenStreetMap Overpass API client.

Overpass rejects requests without a real User-Agent (406) and its main mirror
is frequently busy (504/429). We therefore send a descriptive UA and try a list
of mirrors, retrying each with backoff. A ``BBox`` is (south, west, north, east)
per Overpass convention.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.etl.http import USER_AGENT, FetchError

_log = get_logger("praxis.etl.overpass")

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


@dataclass(frozen=True)
class BBox:
    """Geographic bounding box in EPSG:4326."""

    south: float
    west: float
    north: float
    east: float

    def as_overpass(self) -> str:
        return f"{self.south},{self.west},{self.north},{self.east}"


@retry(
    reraise=True,
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type((httpx.HTTPError,)),
)
def _post(endpoint: str, query: str) -> dict:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=180.0) as client:
        response = client.post(endpoint, data={"data": query})
        response.raise_for_status()
        return response.json()


def run_query(query: str) -> dict:
    """Run an Overpass QL query, trying each mirror until one succeeds."""
    last_error: Exception | None = None
    for endpoint in MIRRORS:
        try:
            _log.info("overpass.query", endpoint=endpoint)
            return _post(endpoint, query)
        except (httpx.HTTPError, ValueError) as exc:
            _log.warning("overpass.mirror_failed", endpoint=endpoint, error=str(exc))
            last_error = exc
    raise FetchError(f"All Overpass mirrors failed: {last_error}")


def amenity_query(bbox: BBox, amenities: list[str], timeout: int = 120) -> str:
    """Build a query for nodes/ways of the given amenity kinds (with centroids)."""
    clauses = "".join(
        f'node["amenity"="{a}"]({bbox.as_overpass()});'
        f'way["amenity"="{a}"]({bbox.as_overpass()});'
        for a in amenities
    )
    return f"[out:json][timeout:{timeout}];({clauses});out center tags;"


def highway_query(bbox: BBox, classes: list[str], timeout: int = 160) -> str:
    """Build a query for road ways of the given highway classes (with geometry)."""
    regex = "|".join(classes)
    return (
        f"[out:json][timeout:{timeout}];"
        f'(way["highway"~"^({regex})$"]({bbox.as_overpass()}););'
        f"out geom tags;"
    )


def parse_amenities(payload: dict) -> list[dict]:
    """Extract point amenities (name, kind, osm id, lat/lon) from a payload."""
    out: list[dict] = []
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:  # way/relation with 'center'
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue
        out.append(
            {
                "osm_id": f"{el['type']}/{el['id']}",
                "name": tags.get("name"),
                "kind": tags.get("amenity", "unknown"),
                "lat": lat,
                "lon": lon,
            }
        )
    return out


def parse_highways(payload: dict) -> list[dict]:
    """Extract road ways (osm id, class, name, coordinate list) from a payload."""
    out: list[dict] = []
    for el in payload.get("elements", []):
        if el.get("type") != "way":
            continue
        geometry = el.get("geometry")
        if not geometry or len(geometry) < 2:
            continue
        tags = el.get("tags", {})
        out.append(
            {
                "osm_id": f"way/{el['id']}",
                "road_class": tags.get("highway"),
                "name": tags.get("name"),
                "coords": [(pt["lon"], pt["lat"]) for pt in geometry],
            }
        )
    return out
