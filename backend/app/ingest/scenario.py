"""Create/refresh the seed scenario and provide scenario lookup helpers."""

from __future__ import annotations

from dataclasses import dataclass

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.etl import seed_manifest as m
from app.etl.provenance import upsert_data_source
from app.models.scenario import Scenario

_log = get_logger("praxis.ingest.scenario")


class ScenarioNotReadyError(RuntimeError):
    """Raised when a pipeline needs the scenario/admin data but it is absent."""


@dataclass(frozen=True)
class Bounds:
    """Scenario extent + representative centre."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    center_lon: float
    center_lat: float


def _seed_district_bounds(session: Session) -> Bounds:
    """Compute the bbox/centre of the seed districts from loaded admin regions."""
    row = session.execute(
        text(
            """
            SELECT ST_XMin(ext), ST_YMin(ext), ST_XMax(ext), ST_YMax(ext),
                   ST_X(ST_Centroid(col)), ST_Y(ST_Centroid(col))
            FROM (
                SELECT ST_Extent(geom) AS ext, ST_Collect(geom) AS col
                FROM admin_region
                WHERE pcode = ANY(:pcodes)
            ) t
            """
        ),
        {"pcodes": list(m.SEED_DISTRICT_PCODES)},
    ).one()
    if row[0] is None:
        raise ScenarioNotReadyError(
            "Seed district admin regions are not loaded; run `ingest admin` first."
        )
    return Bounds(*[float(v) for v in row])


def get_scenario(session: Session) -> Scenario | None:
    """Return the seed scenario row, or None if it has not been created."""
    return session.scalar(select(Scenario).where(Scenario.slug == m.SCENARIO_SLUG))


def require_scenario(session: Session) -> Scenario:
    """Return the seed scenario or fail loudly."""
    scenario = get_scenario(session)
    if scenario is None:
        raise ScenarioNotReadyError(
            "Seed scenario is not present; run `seed-scenario` (or `ingest admin` "
            "then the scenario step) first."
        )
    return scenario


def ensure_scenario(session: Session) -> Scenario:
    """Create or update the seed scenario, deriving its extent from admin data."""
    bounds = _seed_district_bounds(session)
    source = upsert_data_source(
        session,
        key="praxis-seed-manifest",
        name="Praxis seed scenario (2017 SW monsoon floods)",
        url="https://data.humdata.org/dataset/priority-index-sri-lanka-floods-may-2017",
        license="Curated from public records (see docs/DATA_SOURCES.md)",
        notes="Real historical event; hazard/impact layers carry their own sources.",
        is_synthetic=False,
    )

    scenario = get_scenario(session)
    center = from_shape(Point(bounds.center_lon, bounds.center_lat), srid=4326)
    if scenario is None:
        scenario = Scenario(slug=m.SCENARIO_SLUG)
        session.add(scenario)

    scenario.name = m.SCENARIO_NAME
    scenario.hazard_type = m.SCENARIO_HAZARD
    scenario.status = m.SCENARIO_STATUS
    scenario.event_date = m.SCENARIO_EVENT_DATE
    scenario.description = m.SCENARIO_DESCRIPTION
    scenario.bbox_min_lon = bounds.min_lon
    scenario.bbox_min_lat = bounds.min_lat
    scenario.bbox_max_lon = bounds.max_lon
    scenario.bbox_max_lat = bounds.max_lat
    scenario.center = center
    scenario.source_id = source.id
    session.flush()
    _log.info("scenario.ready", slug=scenario.slug, bbox=bounds)
    return scenario
