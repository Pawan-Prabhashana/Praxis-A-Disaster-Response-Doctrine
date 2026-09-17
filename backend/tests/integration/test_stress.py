"""Stress-test API integration tests (require live PostGIS + seed data)."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import engine
from app.db.sync_session import sync_engine
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def postgis() -> Iterator[None]:
    try:
        with sync_engine.connect() as conn:
            if not conn.execute(text("SELECT PostGIS_Version()")).scalar():
                pytest.fail("PostGIS_Version() returned empty")
    except Exception as exc:
        pytest.fail(f"PostGIS not reachable. Run `just db-up && just migrate`. ({exc})")
    yield


@pytest_asyncio.fixture
async def client(postgis: None) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await engine.dispose()


async def _slug(client: AsyncClient) -> str:
    scenarios = (await client.get("/api/v1/scenarios")).json()
    assert scenarios, "Seed scenario missing; run `just data-load`."
    return scenarios[0]["slug"]


async def test_uncertainty_defaults_carry_class_and_basis(client: AsyncClient) -> None:
    slug = await _slug(client)
    cfg = (await client.get(f"/api/v1/scenarios/{slug}/uncertainty-defaults")).json()
    keys = {p["key"] for p in cfg["params"]}
    assert keys == {
        "displacement_rate",
        "at_risk_population",
        "resource_effectiveness",
        "shelter_capacity",
        "closure_realization",
    }
    for p in cfg["params"]:
        assert p["param_class"] in {"real_uncertainty", "assumption", "synthetic_derived"}
        assert p["basis"]  # every parameter states its basis
    # the synthetic-derived one is the road closures
    closure = next(p for p in cfg["params"] if p["key"] == "closure_realization")
    assert closure["param_class"] == "synthetic_derived"


async def test_stress_run_persists_and_is_reproducible(client: AsyncClient) -> None:
    slug = await _slug(client)
    defaults = (await client.get(f"/api/v1/scenarios/{slug}/playbook-defaults")).json()
    pb = (
        await client.post(
            f"/api/v1/scenarios/{slug}/playbooks",
            json={"name": "Stress Integration", "levers": defaults},
        )
    ).json()
    pb_id = pb["id"]
    try:
        body = {"n_iterations": 300, "seed": 4242}
        first = await client.post(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/stress-test", json=body
        )
        assert first.status_code == 201
        r1 = first.json()["result"]
        assert r1["seed"] == 4242
        assert r1["n_iterations"] == 300
        o = r1["overall"]
        assert o["min"] <= o["p05"] <= o["median"] <= o["p95"] <= o["max"]
        assert r1["robustness"]["worst_plausible"] == o["p05"]
        assert 0.0 <= r1["robustness"]["probability_meets_target"] <= 1.0

        # Same seed → identical aggregates (reproducibility).
        second = await client.post(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/stress-test", json=body
        )
        assert second.json()["result"]["overall"] == o

        listed = await client.get(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/stress-runs")
        assert listed.status_code == 200
        assert len(listed.json()) >= 2

        run_id = first.json()["id"]
        detail = await client.get(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/stress-runs/{run_id}"
        )
        assert detail.status_code == 200
        assert detail.json()["id"] == run_id
    finally:
        await client.delete(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}")
