"""Orchestrate the full seed-scenario data load, end to end."""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.sync_session import sync_session
from app.ingest import (
    admin,
    closures,
    desinventar,
    flood,
    gdacs,
    hazard_flood,
    landslide,
    osm,
    weather,
)
from app.ingest.scenario import ensure_scenario

_log = get_logger("praxis.ingest.seed")


def seed_scenario(*, force: bool = False) -> dict[str, int]:
    """Run every pipeline needed to populate the seed scenario, in order.

    Order matters: admin regions first (they define the scenario extent and are
    the spatial-join target), then the scenario, then the layers.
    """
    results: dict[str, int] = {}

    _log.info("seed.step", step="admin")
    results.update(admin.run_admin(force=force))

    _log.info("seed.step", step="scenario")
    with sync_session() as session:
        ensure_scenario(session)

    for step, fn in (
        ("hazard_flood", lambda: hazard_flood.run_hazard_flood(force=force)),
        ("osm", lambda: osm.run_osm(force=force)),
        ("closures", closures.run_closures),
        ("discharge", flood.run_discharge),
        ("weather", weather.run_weather),
        ("desinventar", lambda: desinventar.run_desinventar(force=force)),
        ("landslide", landslide.run_landslide),
        ("gdacs", gdacs.run_gdacs),
    ):
        _log.info("seed.step", step=step)
        results.update(fn())

    _log.info("seed.complete", **results)
    return results
