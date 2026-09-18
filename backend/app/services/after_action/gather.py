"""DB boundary for the after-action review.

Aggregates REAL recorded impact per district from DesInventar ``incident`` rows
(deaths / people affected / houses destroyed, parsed from the incident
description, which the ingest writes in a fixed format), filtered to the
scenario's event year. Returns plain data; the analysis core stays pure.
"""

from __future__ import annotations

from sqlalchemy import ARRAY, String, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.after_action.models import DistrictOutcome, RegionPrediction
from app.services.scoring.models import ScoringInputs

# Recorded impact per district (admin level 2) from REAL incidents only
# (is_synthetic = false), optionally restricted to the event year. Outcome
# numbers are parsed from the fixed-format description the DesInventar ingest
# writes: "... Deaths: N, affected: N, houses destroyed: N."
_OUTCOMES_SQL = text(
    """
    SELECT a.pcode,
           a.name_en AS name,
           count(*) AS incident_count,
           COALESCE(SUM(substring(i.description FROM 'Deaths: ([0-9]+)')::int), 0) AS deaths,
           COALESCE(SUM(substring(i.description FROM 'affected: ([0-9]+)')::int), 0) AS affected,
           COALESCE(
               SUM(substring(i.description FROM 'houses destroyed: ([0-9]+)')::int), 0
           ) AS houses_destroyed
    FROM incident i
    JOIN admin_region a ON a.id = i.admin_region_id AND a.level = 2
    JOIN data_source ds ON ds.id = i.source_id
    WHERE i.scenario_id = :sid
      AND ds.is_synthetic = false
      AND (CAST(:year AS integer) IS NULL
           OR EXTRACT(YEAR FROM i.occurred_at) = CAST(:year AS integer))
      AND a.pcode = ANY(:pcodes)
    GROUP BY a.pcode, a.name_en
    """
).bindparams(bindparam("pcodes", type_=ARRAY(String)))


async def event_year_for(session: AsyncSession, scenario_id: int) -> int | None:
    """The scenario's event year (used to scope recorded outcomes)."""
    row = (
        await session.execute(
            text("SELECT EXTRACT(YEAR FROM event_date)::int FROM scenario WHERE id = :sid"),
            {"sid": scenario_id},
        )
    ).first()
    return int(row[0]) if row and row[0] is not None else None


async def recorded_outcomes(
    session: AsyncSession,
    *,
    scenario_id: int,
    region_names: dict[str, str],
    event_year: int | None,
) -> list[DistrictOutcome]:
    """Real recorded impact per district for the given districts (zeros +
    has_data=False for districts with no records in the window — never a
    fabricated value). ``region_names`` maps pcode -> district name and defines
    the district universe."""
    pcodes = list(region_names)
    if not pcodes:
        return []
    rows = (
        (
            await session.execute(
                _OUTCOMES_SQL, {"sid": scenario_id, "year": event_year, "pcodes": pcodes}
            )
        )
        .mappings()
        .all()
    )
    by_pcode = {r["pcode"]: r for r in rows}
    outcomes: list[DistrictOutcome] = []
    for pcode in pcodes:
        r = by_pcode.get(pcode)
        if r is None:
            outcomes.append(DistrictOutcome(pcode=pcode, name=region_names[pcode], has_data=False))
        else:
            outcomes.append(
                DistrictOutcome(
                    pcode=r["pcode"],
                    name=r["name"],
                    deaths=int(r["deaths"]),
                    affected=int(r["affected"]),
                    houses_destroyed=int(r["houses_destroyed"]),
                    incident_count=int(r["incident_count"]),
                    has_data=int(r["incident_count"]) > 0,
                )
            )
    return outcomes


def predictions_from_inputs(inputs: ScoringInputs) -> list[RegionPrediction]:
    """The strategy's predicted per-district view (from Praxis scoring inputs)."""
    return [
        RegionPrediction(
            pcode=r.pcode,
            name=r.name,
            at_risk_population=round(r.at_risk_population),
            is_priority=r.is_priority,
        )
        for r in inputs.regions
    ]
