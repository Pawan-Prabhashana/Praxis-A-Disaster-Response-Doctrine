"""Resolve a scenario's real data + a playbook's levers into ``ScoringInputs``.

This is the DB/PostGIS boundary. It does the spatial work (areal-weighted at-risk
population, shelter reachability vs. closed roads) and returns plain data. The
pure ``core.score`` never touches the database — Phase 5 will perturb the inputs
produced here and re-score without changing the core.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ARRAY, Integer, String, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.playbook import LeverSet, RegionContext, SheltersInRegions
from app.services.scoring.models import (
    Assumptions,
    RegionInput,
    ResourceInputs,
    ScoringInputs,
    ShelterInputs,
)

# Districts (admin level 2) intersecting the flood extent, with areal-weighted
# at-risk population and whether a closed road crosses them.
#
# This query is heavy (ST_Intersection over the detailed flood extent), so its
# result — which is scenario-level and lever-independent — is memoised per
# scenario in ``_REGION_FACTS_CACHE``. It runs once, then every preview/score is
# a pure lookup. (Data is immutable for a running process; restart after a
# re-``data-load``.)
_REGIONS_SQL = text(
    """
    WITH flood AS (
        SELECT ST_Union(geom) AS g
        FROM hazard_layer
        WHERE scenario_id = :sid AND layer_type = 'flood_extent'
    )
    SELECT a.pcode,
           a.name_en,
           COALESCE(a.population, 0) AS population,
           ST_Area(a.geom::geography) AS area_m2,
           ST_Area(ST_Intersection(a.geom, flood.g)::geography) AS flood_m2,
           EXISTS (
               SELECT 1 FROM road_closure rc
               JOIN road_segment rs ON rs.id = rc.road_segment_id
               WHERE rc.scenario_id = :sid AND ST_Intersects(rs.geom, a.geom)
           ) AS access_impaired
    FROM admin_region a, flood
    WHERE a.level = 2 AND ST_Intersects(a.geom, flood.g)
    ORDER BY a.pcode
    """
)


@dataclass(frozen=True)
class _RegionFact:
    """Cached, lever-independent facts for one district."""

    pcode: str
    name: str
    population: int
    at_risk_population: float
    is_access_impaired: bool


_REGION_FACTS_CACHE: dict[int, list[_RegionFact]] = {}


async def _region_facts(session: AsyncSession, scenario_id: int) -> list[_RegionFact]:
    """Compute (and memoise) the at-risk facts per district for a scenario."""
    cached = _REGION_FACTS_CACHE.get(scenario_id)
    if cached is not None:
        return cached
    rows = (await session.execute(_REGIONS_SQL, {"sid": scenario_id})).mappings().all()
    facts: list[_RegionFact] = []
    for r in rows:
        area = float(r["area_m2"]) or 1.0
        fraction = min(1.0, max(0.0, float(r["flood_m2"]) / area))
        population = int(r["population"])
        facts.append(
            _RegionFact(
                pcode=r["pcode"],
                name=r["name_en"],
                population=population,
                at_risk_population=population * fraction,
                is_access_impaired=bool(r["access_impaired"]),
            )
        )
    _REGION_FACTS_CACHE[scenario_id] = facts
    return facts

# Activated shelters with capacity + reachability vs. closed roads.
# Uses a planar ST_DWithin (degrees) so both GIST indexes apply — far faster than
# casting every geometry to geography. The buffer is passed in degrees.
_SHELTERS_SQL = text(
    """
    WITH closed AS (
        SELECT rs.geom
        FROM road_closure rc
        JOIN road_segment rs ON rs.id = rc.road_segment_id
        WHERE rc.scenario_id = :sid
    )
    SELECT s.id, s.capacity, s.kind,
           NOT EXISTS (
               SELECT 1 FROM closed
               WHERE ST_DWithin(s.geom, closed.geom, :buf_deg)
           ) AS reachable
    FROM shelter s
    WHERE s.id = ANY(:ids)
    """
).bindparams(bindparam("ids", type_=ARRAY(Integer)))

# Approximate metres-per-degree near the equator, for planar distance thresholds.
_METERS_PER_DEGREE = 111_320.0


async def gather_scoring_inputs(
    session: AsyncSession,
    *,
    scenario_id: int,
    levers: LeverSet,
    assumptions: Assumptions | None = None,
) -> ScoringInputs:
    """Build the plain ``ScoringInputs`` for a scenario + lever set."""
    a = assumptions or Assumptions()
    priority = set(levers.priority_region_pcodes)

    facts = await _region_facts(session, scenario_id)
    regions = [
        RegionInput(
            pcode=f.pcode,
            name=f.name,
            population=f.population,
            at_risk_population=f.at_risk_population,
            is_priority=f.pcode in priority,
            is_access_impaired=f.is_access_impaired,
        )
        for f in facts
    ]

    shelters = await _gather_shelters(session, scenario_id, levers.activated_shelter_ids, a)

    return ScoringInputs(
        regions=regions,
        shelters=shelters,
        resources=ResourceInputs(
            response_teams=levers.resources.response_teams,
            boats=levers.resources.boats,
            allocation=levers.resources.allocation,
        ),
        assumptions=a,
        uses_synthetic_closures=True,
    )


async def region_context(session: AsyncSession, *, scenario_id: int) -> list[RegionContext]:
    """Candidate priority regions (districts intersecting the flood) with at-risk."""
    facts = await _region_facts(session, scenario_id)
    out = [
        RegionContext(
            pcode=f.pcode,
            name=f.name,
            population=f.population,
            at_risk_population=round(f.at_risk_population),
            is_access_impaired=f.is_access_impaired,
        )
        for f in facts
    ]
    return sorted(out, key=lambda x: -x.at_risk_population)


# Shelters within districts, resolved through the precomputed shelter→DS-division
# link (level 3) whose parent is the district (level 2). A pure btree join — no
# per-shelter point-in-polygon — so it is fast even over all 1,659 shelters.
_SHELTERS_IN_REGIONS_SQL = text(
    """
    SELECT s.id
    FROM shelter s
    JOIN admin_region ds ON ds.id = s.admin_region_id AND ds.level = 3
    WHERE ds.parent_pcode = ANY(:pcodes)
    ORDER BY s.id
    LIMIT :lim
    """
).bindparams(bindparam("pcodes", type_=ARRAY(String)))

_SHELTERS_COUNT_SQL = text(
    """
    SELECT count(*)
    FROM shelter s
    JOIN admin_region ds ON ds.id = s.admin_region_id AND ds.level = 3
    WHERE ds.parent_pcode = ANY(:pcodes)
    """
).bindparams(bindparam("pcodes", type_=ARRAY(String)))


async def shelters_in_regions(
    session: AsyncSession, *, pcodes: list[str], limit: int
) -> SheltersInRegions:
    """Return candidate shelter ids inside the given regions (capped) and the total."""
    if not pcodes:
        return SheltersInRegions(ids=[], total=0)
    total = int(
        (await session.execute(_SHELTERS_COUNT_SQL, {"pcodes": pcodes})).scalar_one()
    )
    rows = (
        await session.execute(_SHELTERS_IN_REGIONS_SQL, {"pcodes": pcodes, "lim": limit})
    ).all()
    return SheltersInRegions(ids=[int(r[0]) for r in rows], total=total)


async def _gather_shelters(
    session: AsyncSession, scenario_id: int, shelter_ids: list[int], a: Assumptions
) -> ShelterInputs:
    if not shelter_ids:
        return ShelterInputs(
            activated_count=0,
            capacity_known=0.0,
            capacity_assumed=0.0,
            assumed_capacity_count=0,
            reachable_activated_count=0,
        )

    rows = (
        (
            await session.execute(
                _SHELTERS_SQL,
                {
                    "sid": scenario_id,
                    "buf_deg": a.closed_road_buffer_m / _METERS_PER_DEGREE,
                    "ids": shelter_ids,
                },
            )
        )
        .mappings()
        .all()
    )

    capacity_known = 0.0
    capacity_assumed = 0.0
    assumed_count = 0
    reachable = 0
    for row in rows:
        if row["capacity"] is not None:
            capacity_known += float(row["capacity"])
        else:
            kind = row["kind"] or "default"
            capacity_assumed += a.assumed_shelter_capacity.get(
                kind, a.assumed_shelter_capacity["default"]
            )
            assumed_count += 1
        if row["reachable"]:
            reachable += 1

    return ShelterInputs(
        activated_count=len(rows),
        capacity_known=capacity_known,
        capacity_assumed=capacity_assumed,
        assumed_capacity_count=assumed_count,
        reachable_activated_count=reachable,
    )
