"""Demo-seed integration test (requires live PostGIS + loaded seed data).

Verifies the showcase seeding is idempotent and reproduces the robustness
reversal (wide plan wins the point score; focused plan is more robust).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text

from app.db.session import engine
from app.db.sync_session import sync_engine
from app.services.demo.seed import _STRESS_SEED, _run

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def postgis() -> Iterator[None]:
    try:
        with sync_engine.connect() as conn:
            has_regions = conn.execute(text("SELECT count(*) FROM admin_region")).scalar()
            if not has_regions:
                pytest.skip("Seed data not loaded; run `just data-load`.")
    except Exception as exc:
        pytest.fail(f"PostGIS not reachable. Run `just db-up && just migrate`. ({exc})")
    yield


async def test_demo_seed_idempotent_and_reversal(postgis: None) -> None:
    first = await _run()
    names = {name for name, _, _ in first}
    assert names == {"Wide coverage", "Focused & resourced"}

    # Idempotent: a second run creates no duplicate playbooks or stress runs.
    await _run()
    with sync_engine.connect() as conn:
        pb_count = conn.execute(
            text(
                "SELECT count(*) FROM playbook WHERE name IN "
                "('Wide coverage', 'Focused & resourced')"
            )
        ).scalar()
        assert pb_count == 2
        # The robustness reversal: the focused plan's worst-plausible (p05) is
        # higher than the wide plan's, even though the wide plan scores higher.
        rows = conn.execute(
            text(
                """
                SELECT p.name,
                       (sr.result->>'point_overall')::float AS point,
                       (sr.result->'robustness'->>'worst_plausible')::float AS p05
                FROM stress_run sr JOIN playbook p ON p.id = sr.playbook_id
                WHERE sr.seed = :seed
                  AND p.name IN ('Wide coverage', 'Focused & resourced')
                """
            ),
            {"seed": _STRESS_SEED},
        ).all()
    by_name = {r[0]: (r[1], r[2]) for r in rows}
    wide_point, wide_p05 = by_name["Wide coverage"]
    focused_point, focused_p05 = by_name["Focused & resourced"]
    assert wide_point > focused_point  # wide wins the deterministic score
    assert focused_p05 > wide_p05  # focused is the robust choice — the reversal

    await engine.dispose()
