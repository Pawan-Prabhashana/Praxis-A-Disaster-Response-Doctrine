"""Data-driven default lever suggestions, so a new playbook starts smart."""

from __future__ import annotations

import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.playbook import (
    AccessPolicy,
    EvacuationPolicy,
    LeverSet,
    ResourcePosture,
)
from app.services.scoring.gather import _region_facts, shelters_in_regions
from app.services.scoring.models import Assumptions

_TOP_PRIORITY_REGIONS = 3
_MAX_DEFAULT_SHELTERS = 40


async def suggest_default_levers(session: AsyncSession, *, scenario_id: int) -> LeverSet:
    """Suggest a sensible starting strategy from the scenario's real data."""
    a = Assumptions()
    facts = await _region_facts(session, scenario_id)
    ranked = sorted(facts, key=lambda f: -f.at_risk_population)

    top = ranked[:_TOP_PRIORITY_REGIONS]
    priority_pcodes = [f.pcode for f in top]
    covered_at_risk = sum(f.at_risk_population for f in top)
    threshold = int(min((f.at_risk_population for f in top), default=0))

    shelters = await shelters_in_regions(
        session, pcodes=priority_pcodes, limit=_MAX_DEFAULT_SHELTERS
    )
    shelter_ids = shelters.ids

    # Suggest a posture that covers ~half the estimated shelter need — enough to
    # start, leaving visible headroom in the scorecard.
    people_needing = a.displacement_rate * covered_at_risk
    teams = max(5, math.ceil((people_needing * 0.5) / a.team_capacity))
    boats = max(2, math.ceil(teams * 0.4))

    return LeverSet(
        priority_region_pcodes=priority_pcodes,
        activated_shelter_ids=shelter_ids,
        evacuation=EvacuationPolicy(at_risk_threshold=threshold),
        resources=ResourcePosture(
            response_teams=teams, boats=boats, allocation="proportional_to_need"
        ),
        access=AccessPolicy(avoid_closed_roads=True),
    )
