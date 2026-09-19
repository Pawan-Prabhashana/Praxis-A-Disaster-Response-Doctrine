"""Reproducible demo seeding.

Guarantees the two showcase playbooks exist with a stored, fixed-seed stress run
so the two signature demo moments are reproducible on stage every time:

  * the **robustness reversal** — "Wide coverage" wins the deterministic score
    but "Focused & resourced" is the robust choice; and
  * the after-action **inverted alignment** — the wide strategy under-prioritises
    Ratnapura, which recorded the most 2017 deaths.

Idempotent: playbooks are upserted by name and a stress run is only created when
one with the fixed seed does not already exist. Requires the base seed data
(`just data-load`).
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models.playbook import Playbook
from app.models.stress_run import StressRun
from app.schemas.playbook import AccessPolicy, EvacuationPolicy, LeverSet, ResourcePosture
from app.services.scoring.core import score
from app.services.scoring.gather import gather_scoring_inputs, shelters_in_regions
from app.services.scoring.stress import run_stress_test
from app.services.scoring.uncertainty import default_uncertainty_config

# The showcase strategies. Both prioritise Western/Sabaragamuwa districts and
# carry the same resources; the wide plan spreads them across five districts,
# the focused plan concentrates on two (so its resources over-cover — robust).
_SHELTER_LIMIT = 320
_STRESS_SEED = 424242  # fixed so the reversal reproduces byte-for-byte
_N_ITERATIONS = 1000

_SHOWCASE = (
    {
        "name": "Wide coverage",
        "pcodes": ["LK11", "LK13", "LK32", "LK31", "LK91"],  # Colombo…Ratnapura
        "teams": 260,
        "boats": 0,
    },
    {
        "name": "Focused & resourced",
        "pcodes": ["LK11", "LK13"],  # Colombo + Kalutara
        "teams": 260,
        "boats": 0,
    },
)


async def _upsert(session: AsyncSession, scenario_id: int, spec: dict) -> tuple[int, float]:
    shelters = await shelters_in_regions(session, pcodes=spec["pcodes"], limit=_SHELTER_LIMIT)
    levers = LeverSet(
        priority_region_pcodes=spec["pcodes"],
        activated_shelter_ids=shelters.ids,
        evacuation=EvacuationPolicy(),
        resources=ResourcePosture(response_teams=spec["teams"], boats=spec["boats"]),
        access=AccessPolicy(),
    )
    inputs = await gather_scoring_inputs(session, scenario_id=scenario_id, levers=levers)
    result = score(inputs)

    existing = (
        (
            await session.execute(
                select(Playbook).where(
                    Playbook.scenario_id == scenario_id, Playbook.name == spec["name"]
                )
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        existing.levers = levers.model_dump(mode="json")
        existing.score_result = result.model_dump(mode="json")
        pb = existing
    else:
        pb = Playbook(
            scenario_id=scenario_id,
            name=spec["name"],
            levers=levers.model_dump(mode="json"),
            score_result=result.model_dump(mode="json"),
        )
        session.add(pb)
    await session.flush()

    # Ensure a fixed-seed stress run exists (idempotent).
    run = (
        (
            await session.execute(
                select(StressRun).where(
                    StressRun.playbook_id == pb.id, StressRun.seed == _STRESS_SEED
                )
            )
        )
        .scalars()
        .first()
    )
    if run is None:
        config = default_uncertainty_config()
        stress = run_stress_test(inputs, config, n_iterations=_N_ITERATIONS, seed=_STRESS_SEED)
        session.add(
            StressRun(
                scenario_id=scenario_id,
                playbook_id=pb.id,
                n_iterations=_N_ITERATIONS,
                seed=_STRESS_SEED,
                config=config.model_dump(mode="json"),
                result=stress.model_dump(mode="json"),
            )
        )
    return pb.id, result.overall


async def _run() -> list[tuple[str, int, float]]:
    async with SessionLocal() as session:
        row = (await session.execute(text("SELECT id FROM scenario ORDER BY id LIMIT 1"))).first()
        if row is None:
            raise RuntimeError("No scenario found. Run `just data-load` first.")
        scenario_id = int(row[0])
        out: list[tuple[str, int, float]] = []
        for spec in _SHOWCASE:
            pb_id, overall = await _upsert(session, scenario_id, spec)
            out.append((spec["name"], pb_id, overall))
        await session.commit()
        return out


def seed_demo() -> dict[str, str]:
    """Create/refresh the showcase playbooks + stress runs; return a summary."""
    results = asyncio.run(_run())
    return {name: f"id={pb_id} point={overall:.1f}" for name, pb_id, overall in results}
