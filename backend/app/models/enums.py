"""Domain enumerations.

Stored as validated VARCHAR + CHECK constraints (``native_enum=False``) rather
than native PostgreSQL enum types: migrations stay simple (no separate TYPE to
create/alter/drop) and the models remain importable under SQLite for fast unit
tests. Vocabularies that vary widely by source (incident type, shelter kind,
road class) are kept as free strings instead of enums.
"""

from __future__ import annotations

from enum import StrEnum


class HazardType(StrEnum):
    """The hazard a scenario concerns."""

    FLOOD = "flood"
    LANDSLIDE = "landslide"
    CYCLONE = "cyclone"
    MULTI = "multi"


class ScenarioStatus(StrEnum):
    """Lifecycle/nature of a scenario."""

    HISTORICAL = "historical"
    SIMULATED = "simulated"
    LIVE = "live"


class LayerType(StrEnum):
    """Kind of hazard layer geometry."""

    FLOOD_EXTENT = "flood_extent"
    LANDSLIDE_SUSCEPTIBILITY = "landslide_susceptibility"
    CYCLONE_TRACK = "cyclone_track"
    STORM_SURGE = "storm_surge"
