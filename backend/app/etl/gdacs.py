"""GDACS (Global Disaster Alert and Coordination System) current-alerts client.

Fetches the public events feed and extracts point alerts. These are real,
current, global alerts; callers filter to a region of interest. Stored as
reference incidents (scenario-independent), never as historical event data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.etl.http import fetch_json

GDACS_EVENTS = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"


@dataclass(frozen=True)
class GdacsAlert:
    """A single current GDACS alert."""

    external_id: str
    event_type: str
    alert_level: str | None
    title: str
    country: str | None
    occurred_on: date | None
    lat: float
    lon: float


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[: len(fmt) + 2], fmt).date()
        except ValueError:
            continue
    return None


def parse_events(
    payload: dict, *, bbox: tuple[float, float, float, float] | None = None
) -> list[GdacsAlert]:
    """Parse the GDACS FeatureCollection into alerts, optionally clipped to a bbox.

    ``bbox`` is (min_lon, min_lat, max_lon, max_lat).
    """
    out: list[GdacsAlert] = []
    for feat in payload.get("features", []):
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Point" or not coords or len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        if bbox and not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        props = feat.get("properties", {})
        event_id = str(props.get("eventid") or props.get("eventname") or "")
        event_type = str(props.get("eventtype") or "unknown")
        out.append(
            GdacsAlert(
                external_id=f"gdacs:{event_type}:{event_id}",
                event_type=event_type,
                alert_level=props.get("alertlevel"),
                title=str(props.get("name") or props.get("htmldescription") or "GDACS alert"),
                country=props.get("country"),
                occurred_on=_parse_date(props.get("fromdate") or props.get("datemodified")),
                lat=lat,
                lon=lon,
            )
        )
    return out


def fetch_alerts(bbox: tuple[float, float, float, float] | None = None) -> list[GdacsAlert]:
    """Fetch and parse current GDACS alerts (optionally clipped to a bbox)."""
    payload = fetch_json(GDACS_EVENTS, timeout=60.0)
    return parse_events(payload, bbox=bbox)
