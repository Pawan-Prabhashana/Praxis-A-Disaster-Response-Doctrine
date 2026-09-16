"""Open-Meteo clients: GloFAS river discharge (flood) and weather.

No API key required. Parsing is separated from fetching so the parsers can be
unit-tested against recorded payloads with respx (no live network in tests).

Note on ensemble spread: for HISTORICAL dates GloFAS is a deterministic
reanalysis, so the percentile fields equal the deterministic discharge. Genuine
ensemble spread appears only for forward forecasts. We store whatever the API
returns verbatim — never synthesising a spread.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.etl.http import fetch_json

FLOOD_API = "https://flood-api.open-meteo.com/v1/flood"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"

_DISCHARGE_VARS = [
    "river_discharge",
    "river_discharge_mean",
    "river_discharge_median",
    "river_discharge_p25",
    "river_discharge_p75",
    "river_discharge_min",
    "river_discharge_max",
]


@dataclass(frozen=True)
class DischargeDay:
    """One day's ensemble river-discharge statistics (m³/s)."""

    valid_date: date
    mean: float | None
    median: float | None
    p25: float | None
    p75: float | None
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True)
class WeatherDay:
    """One day's weather summary."""

    valid_date: date
    precipitation_mm: float | None
    temperature_c: float | None
    wind_speed_ms: float | None


def _floats(daily: dict, key: str, n: int) -> list[float | None]:
    values = daily.get(key)
    if not isinstance(values, list):
        return [None] * n
    return [v if isinstance(v, int | float) else None for v in values]


def parse_flood(payload: dict) -> list[DischargeDay]:
    """Parse a GloFAS flood API payload into per-day ensemble statistics."""
    daily = payload.get("daily")
    if not daily or "time" not in daily:
        raise ValueError("Open-Meteo flood payload missing 'daily.time'")
    times = daily["time"]
    n = len(times)
    deterministic = _floats(daily, "river_discharge", n)
    mean = _floats(daily, "river_discharge_mean", n)
    median = _floats(daily, "river_discharge_median", n)
    p25 = _floats(daily, "river_discharge_p25", n)
    p75 = _floats(daily, "river_discharge_p75", n)
    dmin = _floats(daily, "river_discharge_min", n)
    dmax = _floats(daily, "river_discharge_max", n)

    out: list[DischargeDay] = []
    for i, t in enumerate(times):
        # Fall back to the deterministic discharge for a missing ensemble mean.
        out.append(
            DischargeDay(
                valid_date=date.fromisoformat(t),
                mean=mean[i] if mean[i] is not None else deterministic[i],
                median=median[i],
                p25=p25[i],
                p75=p75[i],
                minimum=dmin[i],
                maximum=dmax[i],
            )
        )
    return out


def parse_weather(payload: dict) -> list[WeatherDay]:
    """Parse an Open-Meteo daily weather payload."""
    daily = payload.get("daily")
    if not daily or "time" not in daily:
        raise ValueError("Open-Meteo weather payload missing 'daily.time'")
    times = daily["time"]
    n = len(times)
    precip = _floats(daily, "precipitation_sum", n)
    temp = _floats(daily, "temperature_2m_mean", n)
    wind = _floats(daily, "wind_speed_10m_max", n)
    return [
        WeatherDay(
            valid_date=date.fromisoformat(t),
            precipitation_mm=precip[i],
            temperature_c=temp[i],
            wind_speed_ms=wind[i],
        )
        for i, t in enumerate(times)
    ]


def fetch_discharge(
    lat: float, lon: float, start: date, end: date
) -> tuple[list[DischargeDay], float, float]:
    """Fetch river-discharge stats for a point/date range.

    Returns the parsed days plus the grid latitude/longitude Open-Meteo actually
    used (its nearest GloFAS cell), so callers can record the true sample point.
    """
    payload = fetch_json(
        FLOOD_API,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(_DISCHARGE_VARS),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
    )
    return parse_flood(payload), payload.get("latitude", lat), payload.get("longitude", lon)


def fetch_weather(lat: float, lon: float, start: date, end: date) -> list[WeatherDay]:
    """Fetch daily weather for a point/date range.

    Uses the archive endpoint for past ranges (the forecast endpoint only serves
    a recent window) and the forecast endpoint otherwise.
    """
    from datetime import UTC, datetime

    is_historical = end < datetime.now(UTC).date()
    url = ARCHIVE_API if is_historical else WEATHER_API
    payload = fetch_json(
        url,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum,temperature_2m_mean,wind_speed_10m_max",
            "wind_speed_unit": "ms",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "timezone": "auto",
        },
    )
    return parse_weather(payload)
