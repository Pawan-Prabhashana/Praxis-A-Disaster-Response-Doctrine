"""After-action (Learn) endpoints: recorded outcomes, build/persist, list, fetch."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models.after_action import AfterAction
from app.models.playbook import Playbook
from app.schemas.after_action import (
    AfterActionListItem,
    AfterActionRead,
    AfterActionRequest,
    RecordedOutcomesResponse,
)
from app.schemas.playbook import LeverSet
from app.services.after_action.analysis import build_after_action
from app.services.after_action.gather import (
    event_year_for,
    predictions_from_inputs,
    recorded_outcomes,
)
from app.services.after_action.lessons import LessonsContent, generate_lessons
from app.services.after_action.models import AfterActionResult
from app.services.scoring.gather import gather_scoring_inputs

router = APIRouter(prefix="/scenarios/{slug}", tags=["after-action"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def _scenario_id(slug: str, session: AsyncSession) -> int:
    row = (
        await session.execute(text("SELECT id FROM scenario WHERE slug = :slug"), {"slug": slug})
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{slug}' not found")
    return int(row[0])


async def _get_playbook(session: AsyncSession, scenario_id: int, playbook_id: int) -> Playbook:
    pb = await session.get(Playbook, playbook_id)
    if pb is None or pb.scenario_id != scenario_id:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return pb


async def _region_names(
    session: AsyncSession, scenario_id: int, levers: LeverSet
) -> dict[str, str]:
    inputs = await gather_scoring_inputs(session, scenario_id=scenario_id, levers=levers)
    return {r.pcode: r.name for r in inputs.regions}


@router.get(
    "/recorded-outcomes",
    response_model=RecordedOutcomesResponse,
    summary="Real recorded impact per district (actual historical baseline)",
)
async def get_recorded_outcomes(slug: str, session: SessionDep) -> RecordedOutcomesResponse:
    scenario_id = await _scenario_id(slug, session)
    year = await event_year_for(session, scenario_id)
    # Universe = the flood-affected districts Praxis scores (empty levers → all
    # districts present, none prioritised — we only need the pcode/name set).
    names = await _region_names(session, scenario_id, LeverSet())
    outcomes = await recorded_outcomes(
        session, scenario_id=scenario_id, region_names=names, event_year=year
    )
    totals = {
        "deaths": sum(o.deaths for o in outcomes),
        "affected": sum(o.affected for o in outcomes),
        "houses_destroyed": sum(o.houses_destroyed for o in outcomes),
        "incident_count": sum(o.incident_count for o in outcomes),
        "districts_with_data": sum(1 for o in outcomes if o.has_data),
    }
    return RecordedOutcomesResponse(
        scenario_slug=slug, event_year=year, districts=outcomes, totals=totals
    )


async def _build(session: AsyncSession, scenario_id: int, slug: str, pb: Playbook):
    levers = LeverSet.model_validate(pb.levers)
    inputs = await gather_scoring_inputs(session, scenario_id=scenario_id, levers=levers)
    predictions = predictions_from_inputs(inputs)
    year = await event_year_for(session, scenario_id)
    outcomes = await recorded_outcomes(
        session,
        scenario_id=scenario_id,
        region_names={p.pcode: p.name for p in predictions},
        event_year=year,
    )
    return build_after_action(slug, pb.name, year, predictions, outcomes)


def _to_read(aa: AfterAction, slug: str) -> AfterActionRead:
    return AfterActionRead(
        id=aa.id,
        scenario_slug=slug,
        playbook_id=aa.playbook_id,
        brief_id=aa.brief_id,
        stress_run_id=aa.stress_run_id,
        event_year=aa.event_year,
        generator=aa.generator,
        model=aa.model,
        created_at=aa.created_at,
        result=AfterActionResult.model_validate(aa.result),
        lessons=LessonsContent.model_validate(aa.lessons),
    )


@router.post(
    "/playbooks/{playbook_id}/after-action",
    response_model=AfterActionRead,
    status_code=201,
    summary="Build and persist a predicted-vs-recorded after-action review",
)
async def create_after_action(
    slug: str,
    playbook_id: int,
    payload: AfterActionRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> AfterActionRead:
    scenario_id = await _scenario_id(slug, session)
    pb = await _get_playbook(session, scenario_id, playbook_id)
    result = await _build(session, scenario_id, slug, pb)
    lessons = await generate_lessons(result, settings)

    aa = AfterAction(
        scenario_id=scenario_id,
        playbook_id=playbook_id,
        brief_id=payload.brief_id,
        stress_run_id=payload.stress_run_id,
        event_year=result.event_year,
        generator=lessons.generator,
        model=lessons.model,
        result=result.model_dump(mode="json"),
        lessons=lessons.model_dump(mode="json"),
    )
    session.add(aa)
    await session.commit()
    await session.refresh(aa)
    return _to_read(aa, slug)


@router.get(
    "/playbooks/{playbook_id}/after-actions",
    response_model=list[AfterActionListItem],
    summary="List a playbook's after-action reviews (newest first)",
)
async def list_after_actions(
    slug: str, playbook_id: int, session: SessionDep
) -> list[AfterActionListItem]:
    scenario_id = await _scenario_id(slug, session)
    await _get_playbook(session, scenario_id, playbook_id)
    rows = (
        (
            await session.execute(
                select(AfterAction)
                .where(AfterAction.playbook_id == playbook_id)
                .order_by(AfterAction.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        AfterActionListItem(
            id=aa.id,
            playbook_id=aa.playbook_id,
            event_year=aa.event_year,
            generator=aa.generator,
            alignment_label=str(aa.result.get("alignment", {}).get("label", "")),
            created_at=aa.created_at,
        )
        for aa in rows
    ]


@router.get(
    "/playbooks/{playbook_id}/after-actions/{aa_id}",
    response_model=AfterActionRead,
    summary="Get one after-action review",
)
async def get_after_action(
    slug: str, playbook_id: int, aa_id: int, session: SessionDep
) -> AfterActionRead:
    scenario_id = await _scenario_id(slug, session)
    await _get_playbook(session, scenario_id, playbook_id)
    aa = await session.get(AfterAction, aa_id)
    if aa is None or aa.playbook_id != playbook_id:
        raise HTTPException(status_code=404, detail=f"After-action {aa_id} not found")
    return _to_read(aa, slug)
