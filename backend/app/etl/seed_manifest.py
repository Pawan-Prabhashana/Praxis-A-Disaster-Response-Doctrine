"""Seed scenario manifest — the one real historical event Praxis ships with.

Committed (small, code-shaped) so the demo is reproducible. Geodata itself is
downloaded on demand into the git-ignored cache; only these definitions live in
the repo.

Event: the May 2017 South-West Monsoon floods, which devastated the Kalu Ganga
basin (Ratnapura + Kalutara) — the canonical modern Sri Lankan flood disaster
with openly downloadable satellite flood extent (Netherlands Red Cross via HDX).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

SCENARIO_SLUG = "2017-sw-monsoon-kalu-ganga"
SCENARIO_NAME = "2017 South-West Monsoon Floods — Kalu Ganga Basin"
SCENARIO_HAZARD = "flood"
SCENARIO_STATUS = "historical"
SCENARIO_EVENT_DATE = date(2017, 5, 26)
SCENARIO_DESCRIPTION = (
    "In late May 2017 the south-west monsoon brought extreme rainfall to "
    "south-western Sri Lanka. The Kalu Ganga burst its banks, causing severe "
    "flooding and landslides across Ratnapura and Kalutara and neighbouring "
    "districts — among the worst flood disasters in the country's recent "
    "history. This scenario assembles the real admin geography, satellite flood "
    "extent, river-discharge record, rainfall, and historical loss data for the "
    "affected basin."
)

# Districts (COD-AB adm2 P-codes) that scope the scenario. GN divisions (adm4)
# are loaded only for these districts to keep payloads and load time sane.
SEED_DISTRICT_PCODES: tuple[str, ...] = (
    "LK91",  # Ratnapura (Sabaragamuwa) — Kalu Ganga headwaters
    "LK13",  # Kalutara (Western) — Kalu Ganga mouth
    "LK31",  # Galle (Southern)
    "LK32",  # Matara (Southern)
    "LK11",  # Colombo (Western)
)

# Discharge / weather window around the event (rise → peak → recession).
EVENT_START = date(2017, 5, 14)
EVENT_END = date(2017, 6, 3)


@dataclass(frozen=True)
class RiverPointDef:
    """A Kalu Ganga basin river location to fetch discharge for."""

    key: str
    name: str
    river_name: str
    lat: float
    lon: float


# Real gauging locations along the Kalu Ganga and its tributaries (coordinates
# approximate; Open-Meteo snaps each to the nearest GloFAS grid cell and the
# actual sampled cell is recorded).
RIVER_POINTS: tuple[RiverPointDef, ...] = (
    RiverPointDef("kalu-ratnapura", "Ratnapura", "Kalu Ganga", 6.706, 80.384),
    RiverPointDef("kalu-ellagawa", "Ellagawa", "Kalu Ganga", 6.731, 80.170),
    RiverPointDef("kalu-putupaula", "Putupaula", "Kalu Ganga", 6.717, 80.100),
    RiverPointDef("kalu-millakanda", "Millakanda", "Kuda Ganga", 6.600, 80.230),
    RiverPointDef("kalu-magura", "Magura", "Kalu Ganga", 6.560, 80.100),
    RiverPointDef("kalu-kalutara", "Kalutara", "Kalu Ganga", 6.583, 79.960),
)


@dataclass(frozen=True)
class WeatherPointDef:
    """A location to sample rainfall/temperature for."""

    key: str
    name: str
    lat: float
    lon: float


WEATHER_POINTS: tuple[WeatherPointDef, ...] = (
    WeatherPointDef("wx-ratnapura", "Ratnapura", 6.706, 80.384),
    WeatherPointDef("wx-kalutara", "Kalutara", 6.583, 79.960),
    WeatherPointDef("wx-galle", "Galle", 6.053, 80.220),
)
