"""Unit tests for the GDACS events parser (no live network)."""

from __future__ import annotations

from datetime import date

from app.etl.gdacs import parse_events


def test_parse_events_extracts_points_and_clips_bbox() -> None:
    payload = {
        "features": [
            {
                "geometry": {"type": "Point", "coordinates": [80.0, 6.5]},
                "properties": {
                    "eventid": "1",
                    "eventtype": "FL",
                    "alertlevel": "Orange",
                    "name": "Sri Lanka flood",
                    "country": "Sri Lanka",
                    "fromdate": "2017-05-26T00:00:00",
                },
            },
            {
                "geometry": {"type": "Point", "coordinates": [14.0, 48.0]},
                "properties": {"eventid": "2", "eventtype": "EQ", "name": "Europe quake"},
            },
        ]
    }
    alerts = parse_events(payload, bbox=(60.0, 0.0, 100.0, 35.0))
    assert len(alerts) == 1
    assert alerts[0].external_id == "gdacs:FL:1"
    assert alerts[0].alert_level == "Orange"
    assert alerts[0].occurred_on == date(2017, 5, 26)
    assert alerts[0].lat == 6.5
