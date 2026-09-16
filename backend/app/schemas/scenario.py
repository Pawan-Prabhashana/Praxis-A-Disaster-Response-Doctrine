"""Schemas for scenario endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ScenarioListItem(BaseModel):
    """Summary row for the scenario list / selector."""

    id: int
    slug: str
    name: str
    hazard_type: str
    status: str
    event_date: date | None


class SourceInfo(BaseModel):
    """Provenance entry attached to a scenario."""

    key: str
    name: str
    license: str | None
    is_synthetic: bool


class BBox(BaseModel):
    """Geographic bounds [min_lon, min_lat, max_lon, max_lat]."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


class LonLat(BaseModel):
    """A longitude/latitude pair."""

    lon: float
    lat: float


class ScenarioDetail(BaseModel):
    """Full scenario detail: identity, extent, layer availability, provenance."""

    id: int
    slug: str
    name: str
    hazard_type: str
    status: str
    event_date: date | None
    description: str | None
    bbox: BBox | None
    center: LonLat | None
    layers: dict[str, int] = Field(description="Row counts of layers available for this scenario.")
    sources: list[SourceInfo] = Field(description="Provenance for the scenario's data.")
