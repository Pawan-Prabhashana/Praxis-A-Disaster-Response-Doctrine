"""Unit tests for Open-Meteo / GloFAS parsing (no live network)."""

from __future__ import annotations

from datetime import date

import httpx
import respx

from app.etl.openmeteo import (
    ARCHIVE_API,
    FLOOD_API,
    fetch_discharge,
    fetch_weather,
    parse_flood,
    parse_weather,
)

_FLOOD_ENSEMBLE = {
    "latitude": 6.7,
    "longitude": 80.4,
    "daily": {
        "time": ["2017-05-25", "2017-05-26"],
        "river_discharge": [120.0, 340.5],
        "river_discharge_mean": [118.0, 330.0],
        "river_discharge_median": [115.0, 325.0],
        "river_discharge_p25": [90.0, 280.0],
        "river_discharge_p75": [140.0, 390.0],
        "river_discharge_min": [70.0, 210.0],
        "river_discharge_max": [180.0, 480.0],
    },
}

_FLOOD_DETERMINISTIC = {
    "latitude": 6.7,
    "longitude": 80.4,
    "daily": {
        "time": ["2017-05-26"],
        "river_discharge": [340.5],
    },
}

_WEATHER = {
    "daily": {
        "time": ["2017-05-25", "2017-05-26"],
        "precipitation_sum": [12.4, 88.1],
        "temperature_2m_mean": [26.1, 24.8],
        "wind_speed_10m_max": [4.2, 7.5],
    },
}


def test_parse_flood_ensemble_stats() -> None:
    days = parse_flood(_FLOOD_ENSEMBLE)
    assert len(days) == 2
    peak = days[1]
    assert peak.valid_date == date(2017, 5, 26)
    assert peak.mean == 330.0
    assert peak.median == 325.0
    assert peak.p25 == 280.0
    assert peak.p75 == 390.0
    assert peak.minimum == 210.0
    assert peak.maximum == 480.0


def test_parse_flood_falls_back_to_deterministic_mean() -> None:
    days = parse_flood(_FLOOD_DETERMINISTIC)
    assert days[0].mean == 340.5
    # Missing ensemble fields stay None — we never invent a spread.
    assert days[0].p25 is None
    assert days[0].maximum is None


def test_parse_flood_rejects_empty_payload() -> None:
    try:
        parse_flood({})
    except ValueError as exc:
        assert "daily.time" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_parse_weather_daily_variables() -> None:
    days = parse_weather(_WEATHER)
    assert days[0].precipitation_mm == 12.4
    assert days[1].temperature_c == 24.8
    assert days[1].wind_speed_ms == 7.5


@respx.mock
def test_fetch_discharge_uses_flood_api() -> None:
    respx.get(FLOOD_API).mock(return_value=httpx.Response(200, json=_FLOOD_ENSEMBLE))
    days, lat, lon = fetch_discharge(6.706, 80.384, date(2017, 5, 25), date(2017, 5, 26))
    assert lat == 6.7
    assert lon == 80.4
    assert days[1].mean == 330.0


@respx.mock
def test_fetch_weather_uses_archive_for_historical_range() -> None:
    respx.get(ARCHIVE_API).mock(return_value=httpx.Response(200, json=_WEATHER))
    days = fetch_weather(6.706, 80.384, date(2017, 5, 25), date(2017, 5, 26))
    assert days[1].precipitation_mm == 88.1
