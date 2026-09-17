"""Playbook CRUD, scoring, and default-suggestion endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.playbook import Playbook
from app.schemas.playbook import (
    LeverSet,
    PlaybookCreate,
    PlaybookRead,
    PlaybookUpdate,
    RegionContext,
    SheltersInRegions,
)
from app.services.scoring.core import score
from app.services.scoring.defaults import suggest_default_levers
from app.services.scoring.gather import (
    gather_scoring_inputs,
    region_context,
    shelters_in_regions,
)
from app.services.scoring.models import ScoreResult

_MAX_SHELTER_ACTIVATION = 500

router = APIRouter(prefix="/scenarios/{slug}", tags=["playbooks"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _scenario_id(slug: str, session: AsyncSession) -> int:
    row = (
        await session.execute(text("SELECT id FROM scenario WHERE slug = :slug"), {"slug": slug})
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{slug}' not found")
    return int(row[0])


async def _score_levers(session: AsyncSession, scenario_id: int, levers: LeverSet) -> ScoreResult:
    inputs = await gather_scoring_inputs(session, scenario_id=scenario_id, levers=levers)
    return score(inputs)


def _to_read(pb: Playbook, slug: str) -> PlaybookRead:
    return PlaybookRead(
        id=pb.id,
        scenario_slug=slug,
        name=pb.name,
        description=pb.description,
        levers=LeverSet.model_validate(pb.levers),
        score_result=ScoreResult.model_validate(pb.score_result) if pb.score_result else None,
        created_at=pb.created_at,
        updated_at=pb.updated_at,
    )


async def _get_playbook(session: AsyncSession, scenario_id: int, playbook_id: int) -> Playbook:
    pb = await session.get(Playbook, playbook_id)
    if pb is None or pb.scenario_id != scenario_id:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return pb


@router.get("/playbook-defaults", response_model=LeverSet, summary="Suggested starting levers")
async def playbook_defaults(slug: str, session: SessionDep) -> LeverSet:
    scenario_id = await _scenario_id(slug, session)
    return await suggest_default_levers(session, scenario_id=scenario_id)


@router.get(
    "/playbook-context",
    response_model=list[RegionContext],
    summary="Candidate priority regions with population + at-risk",
)
async def playbook_context(slug: str, session: SessionDep) -> list[RegionContext]:
    scenario_id = await _scenario_id(slug, session)
    return await region_context(session, scenario_id=scenario_id)


@router.get(
    "/shelters-in-regions",
    response_model=SheltersInRegions,
    summary="Candidate shelter ids within the given regions",
)
async def shelters_in_regions_endpoint(
    slug: str, session: SessionDep, pcodes: str = "", limit: int = _MAX_SHELTER_ACTIVATION
) -> SheltersInRegions:
    await _scenario_id(slug, session)
    codes = [c for c in (p.strip() for p in pcodes.split(",")) if c]
    return await shelters_in_regions(
        session, pcodes=codes, limit=min(limit, _MAX_SHELTER_ACTIVATION)
    )


@router.post(
    "/playbooks/preview-score",
    response_model=ScoreResult,
    summary="Score a lever set without saving (live preview)",
)
async def preview_score(slug: str, levers: LeverSet, session: SessionDep) -> ScoreResult:
    scenario_id = await _scenario_id(slug, session)
    return await _score_levers(session, scenario_id, levers)


@router.get("/playbooks", response_model=list[PlaybookRead], summary="List playbooks")
async def list_playbooks(slug: str, session: SessionDep) -> list[PlaybookRead]:
    scenario_id = await _scenario_id(slug, session)
    rows = (
        (
            await session.execute(
                select(Playbook)
                .where(Playbook.scenario_id == scenario_id)
                .order_by(Playbook.created_at)
            )
        )
        .scalars()
        .all()
    )
    return [_to_read(pb, slug) for pb in rows]


@router.post(
    "/playbooks",
    response_model=PlaybookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a playbook (scores on write)",
)
async def create_playbook(slug: str, payload: PlaybookCreate, session: SessionDep) -> PlaybookRead:
    scenario_id = await _scenario_id(slug, session)
    result = await _score_levers(session, scenario_id, payload.levers)
    pb = Playbook(
        scenario_id=scenario_id,
        name=payload.name,
        description=payload.description,
        levers=payload.levers.model_dump(mode="json"),
        score_result=result.model_dump(mode="json"),
    )
    session.add(pb)
    await session.commit()
    await session.refresh(pb)
    return _to_read(pb, slug)


@router.get("/playbooks/{playbook_id}", response_model=PlaybookRead, summary="Get a playbook")
async def get_playbook(slug: str, playbook_id: int, session: SessionDep) -> PlaybookRead:
    scenario_id = await _scenario_id(slug, session)
    pb = await _get_playbook(session, scenario_id, playbook_id)
    return _to_read(pb, slug)


@router.put("/playbooks/{playbook_id}", response_model=PlaybookRead, summary="Update a playbook")
async def update_playbook(
    slug: str, playbook_id: int, payload: PlaybookUpdate, session: SessionDep
) -> PlaybookRead:
    scenario_id = await _scenario_id(slug, session)
    pb = await _get_playbook(session, scenario_id, playbook_id)
    if payload.name is not None:
        pb.name = payload.name
    if payload.description is not None:
        pb.description = payload.description
    if payload.levers is not None:
        pb.levers = payload.levers.model_dump(mode="json")
        result = await _score_levers(session, scenario_id, payload.levers)
        pb.score_result = result.model_dump(mode="json")
    await session.commit()
    await session.refresh(pb)
    return _to_read(pb, slug)


@router.delete(
    "/playbooks/{playbook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a playbook",
)
async def delete_playbook(slug: str, playbook_id: int, session: SessionDep) -> Response:
    scenario_id = await _scenario_id(slug, session)
    pb = await _get_playbook(session, scenario_id, playbook_id)
    await session.delete(pb)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/playbooks/{playbook_id}/score",
    response_model=ScoreResult,
    summary="Recompute and cache a playbook's scorecard",
)
async def score_playbook(slug: str, playbook_id: int, session: SessionDep) -> ScoreResult:
    scenario_id = await _scenario_id(slug, session)
    pb = await _get_playbook(session, scenario_id, playbook_id)
    result = await _score_levers(session, scenario_id, LeverSet.model_validate(pb.levers))
    pb.score_result = result.model_dump(mode="json")
    await session.commit()
    return result
