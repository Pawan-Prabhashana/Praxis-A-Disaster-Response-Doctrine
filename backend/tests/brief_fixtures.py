"""Shared, DB-free fixtures for brief unit tests."""

from __future__ import annotations

from datetime import date

from app.schemas.playbook import (
    AccessPolicy,
    EvacuationPolicy,
    LeverSet,
    ResourcePosture,
)
from app.services.brief.facts import BriefFacts, ScenarioFacts, build_brief_facts
from app.services.scoring.core import score
from app.services.scoring.models import (
    Assumptions,
    RegionInput,
    ResourceInputs,
    ScoringInputs,
    ShelterInputs,
)


def make_inputs() -> ScoringInputs:
    return ScoringInputs(
        regions=[
            RegionInput(
                pcode="LK11",
                name="Colombo",
                population=2459998,
                at_risk_population=367562,
                is_priority=True,
                is_access_impaired=True,
            ),
            RegionInput(
                pcode="LK13",
                name="Kalutara",
                population=1278998,
                at_risk_population=181445,
                is_priority=True,
                is_access_impaired=False,
            ),
            RegionInput(
                pcode="LK32",
                name="Galle",
                population=1139000,
                at_risk_population=108294,
                is_priority=False,
                is_access_impaired=False,
            ),
        ],
        shelters=ShelterInputs(
            activated_count=200,
            capacity_known=0.0,
            capacity_assumed=60000.0,
            assumed_capacity_count=200,
            reachable_activated_count=180,
        ),
        resources=ResourceInputs(response_teams=260, boats=0, allocation="proportional_to_need"),
        assumptions=Assumptions(),
    )


def make_levers() -> LeverSet:
    return LeverSet(
        priority_region_pcodes=["LK11", "LK13"],
        activated_shelter_ids=list(range(200)),
        evacuation=EvacuationPolicy(at_risk_threshold=50000),
        resources=ResourcePosture(response_teams=260, boats=0),
        access=AccessPolicy(avoid_closed_roads=True),
    )


def make_scenario() -> ScenarioFacts:
    return ScenarioFacts(
        slug="2017-sw-monsoon-kalu-ganga",
        name="2017 SW-Monsoon Floods",
        hazard_type="flood",
        status="historical",
        event_date=date(2017, 5, 26),
        description="Monsoon floods in the Kalu Ganga basin.",
    )


def make_facts() -> BriefFacts:
    inputs = make_inputs()
    return build_brief_facts(
        scenario=make_scenario(),
        playbook_name="Wide coverage",
        playbook_description=None,
        levers=make_levers(),
        inputs=inputs,
        score_result=score(inputs),
        stress_result=None,
    )
