"""Schemas for river discharge (ensemble) endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DischargeDay(BaseModel):
    """One day's ensemble discharge statistics (m³/s)."""

    valid_date: date
    mean: float | None
    median: float | None
    p25: float | None
    p75: float | None
    min: float | None
    max: float | None


class RiverPointDischarge(BaseModel):
    """A river point and its discharge series."""

    river_point_id: int
    key: str
    name: str
    river_name: str | None
    lon: float
    lat: float
    source: str
    is_synthetic: bool
    series: list[DischargeDay]


class DischargeResponse(BaseModel):
    """Discharge series for one or more river points in a scenario."""

    scenario_slug: str
    points: list[RiverPointDischarge] = Field(default_factory=list)
