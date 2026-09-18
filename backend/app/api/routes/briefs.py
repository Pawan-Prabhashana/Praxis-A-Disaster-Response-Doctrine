"""Operational-brief endpoints (Phase 6 — Act): generate, list, fetch, export."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.models.brief import Brief
from app.models.playbook import Playbook
from app.models.stress_run import StressRun
from app.schemas.brief import BriefListItem, BriefRead, BriefRequest
from app.schemas.playbook import LeverSet
from app.services.brief.content import BriefContent
from app.services.brief.facts import BriefFacts, ScenarioFacts, build_brief_facts
from app.services.brief.generator import generate_brief
from app.services.brief.guard import GuardReport
from app.services.brief.render import render_html, render_pdf
from app.services.scoring.core import score
from app.services.scoring.gather import gather_scoring_inputs
from app.services.scoring.stress import StressResult

router = APIRouter(prefix="/scenarios/{slug}", tags=["briefs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def _scenario_facts(slug: str, session: AsyncSession) -> tuple[int, ScenarioFacts]:
    row = (
        await session.execute(
            text(
                """
                SELECT id, slug, name, hazard_type, status, event_date, description
                FROM scenario WHERE slug = :slug
                """
            ),
            {"slug": slug},
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{slug}' not found")
    m = row._mapping
    facts = ScenarioFacts(
        slug=m["slug"],
        name=m["name"],
        hazard_type=m["hazard_type"],
        status=m["status"],
        event_date=m["event_date"],
        description=m["description"],
    )
    return int(m["id"]), facts


async def _get_playbook(session: AsyncSession, scenario_id: int, playbook_id: int) -> Playbook:
    pb = await session.get(Playbook, playbook_id)
    if pb is None or pb.scenario_id != scenario_id:
        raise HTTPException(status_code=404, detail=f"Playbook {playbook_id} not found")
    return pb


async def _resolve_stress(
    session: AsyncSession, playbook_id: int, stress_run_id: int | None
) -> StressRun | None:
    """The requested run, else the playbook's most recent run, else None."""
    if stress_run_id is not None:
        run = await session.get(StressRun, stress_run_id)
        if run is None or run.playbook_id != playbook_id:
            raise HTTPException(status_code=404, detail=f"Stress run {stress_run_id} not found")
        return run
    return (
        (
            await session.execute(
                select(StressRun)
                .where(StressRun.playbook_id == playbook_id)
                .order_by(StressRun.created_at.desc())
                .limit(1)
            )
        )
        .scalars()
        .first()
    )


async def _build_facts(
    session: AsyncSession, scenario_id: int, scenario_facts: ScenarioFacts, pb: Playbook, run
) -> tuple[BriefFacts, StressRun | None]:
    levers = LeverSet.model_validate(pb.levers)
    inputs = await gather_scoring_inputs(session, scenario_id=scenario_id, levers=levers)
    score_result = score(inputs)
    stress_result = StressResult.model_validate(run.result) if run is not None else None
    facts = build_brief_facts(
        scenario=scenario_facts,
        playbook_name=pb.name,
        playbook_description=pb.description,
        levers=levers,
        inputs=inputs,
        score_result=score_result,
        stress_result=stress_result,
    )
    return facts, run


def _to_read(brief: Brief, slug: str) -> BriefRead:
    return BriefRead(
        id=brief.id,
        scenario_slug=slug,
        playbook_id=brief.playbook_id,
        stress_run_id=brief.stress_run_id,
        generator=brief.generator,
        model=brief.model,
        created_at=brief.created_at,
        facts=BriefFacts.model_validate(brief.facts),
        content=BriefContent.model_validate(brief.content),
        guard=GuardReport.model_validate(brief.guard),
    )


@router.post("/playbooks/{playbook_id}/brief", response_model=BriefRead, status_code=201)
async def create_brief(
    slug: str,
    playbook_id: int,
    payload: BriefRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> BriefRead:
    scenario_id, scenario_facts = await _scenario_facts(slug, session)
    pb = await _get_playbook(session, scenario_id, playbook_id)
    run = await _resolve_stress(session, playbook_id, payload.stress_run_id)
    facts, run = await _build_facts(session, scenario_id, scenario_facts, pb, run)

    generated = await generate_brief(facts, settings)

    brief = Brief(
        scenario_id=scenario_id,
        playbook_id=playbook_id,
        stress_run_id=run.id if run is not None else None,
        generator=generated.generator,
        model=generated.model,
        facts=facts.model_dump(mode="json"),
        content=generated.content.model_dump(mode="json"),
        guard=generated.guard.model_dump(mode="json"),
    )
    session.add(brief)
    await session.commit()
    await session.refresh(brief)
    return _to_read(brief, slug)


@router.get("/playbooks/{playbook_id}/briefs", response_model=list[BriefListItem])
async def list_briefs(slug: str, playbook_id: int, session: SessionDep) -> list[BriefListItem]:
    scenario_id, _ = await _scenario_facts(slug, session)
    await _get_playbook(session, scenario_id, playbook_id)
    rows = (
        (
            await session.execute(
                select(Brief)
                .where(Brief.playbook_id == playbook_id)
                .order_by(Brief.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        BriefListItem(
            id=b.id,
            playbook_id=b.playbook_id,
            stress_run_id=b.stress_run_id,
            generator=b.generator,
            model=b.model,
            headline=str(b.content.get("headline", "Operational brief")),
            created_at=b.created_at,
        )
        for b in rows
    ]


async def _load_brief(session: AsyncSession, slug: str, playbook_id: int, brief_id: int) -> Brief:
    scenario_id, _ = await _scenario_facts(slug, session)
    await _get_playbook(session, scenario_id, playbook_id)
    brief = await session.get(Brief, brief_id)
    if brief is None or brief.playbook_id != playbook_id:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")
    return brief


@router.get("/playbooks/{playbook_id}/briefs/{brief_id}", response_model=BriefRead)
async def get_brief(slug: str, playbook_id: int, brief_id: int, session: SessionDep) -> BriefRead:
    brief = await _load_brief(session, slug, playbook_id, brief_id)
    return _to_read(brief, slug)


def _render_meta(brief: Brief) -> dict[str, object]:
    guard = brief.guard or {}
    repaired = len(guard.get("repaired_sections", []) or [])
    return {
        "model": brief.model,
        "guard_repaired": repaired,
        "generated_at": brief.created_at.strftime("%Y-%m-%d %H:%M UTC"),
    }


@router.get("/playbooks/{playbook_id}/briefs/{brief_id}/export.html", response_class=HTMLResponse)
async def export_brief_html(
    slug: str, playbook_id: int, brief_id: int, session: SessionDep
) -> HTMLResponse:
    brief = await _load_brief(session, slug, playbook_id, brief_id)
    html = render_html(
        BriefFacts.model_validate(brief.facts),
        BriefContent.model_validate(brief.content),
        _render_meta(brief),
    )
    return HTMLResponse(content=html)


@router.get("/playbooks/{playbook_id}/briefs/{brief_id}/export.pdf")
async def export_brief_pdf(
    slug: str, playbook_id: int, brief_id: int, session: SessionDep
) -> Response:
    brief = await _load_brief(session, slug, playbook_id, brief_id)
    pdf = render_pdf(
        BriefFacts.model_validate(brief.facts),
        BriefContent.model_validate(brief.content),
        _render_meta(brief),
    )
    filename = f"praxis-brief-{brief_id}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
