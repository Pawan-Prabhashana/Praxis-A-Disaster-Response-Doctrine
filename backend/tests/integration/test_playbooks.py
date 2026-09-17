"""Playbook API integration tests (require live PostGIS + seed data)."""

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
    # Dispose the shared async engine so pooled connections aren't reused across
    # per-test event loops (pytest-asyncio uses a fresh loop per test).
    await engine.dispose()


async def _slug(client: AsyncClient) -> str:
    scenarios = (await client.get("/api/v1/scenarios")).json()
    assert scenarios, "Seed scenario missing; run `just data-load`."
    return scenarios[0]["slug"]


async def test_defaults_are_data_driven(client: AsyncClient) -> None:
    slug = await _slug(client)
    resp = await client.get(f"/api/v1/scenarios/{slug}/playbook-defaults")
    assert resp.status_code == 200
    levers = resp.json()
    assert levers["priority_region_pcodes"], "expected suggested priority regions"
    assert levers["activated_shelter_ids"], "expected suggested shelters"
    assert levers["resources"]["response_teams"] > 0


async def test_preview_score_is_transparent_and_flagged(client: AsyncClient) -> None:
    slug = await _slug(client)
    levers = (await client.get(f"/api/v1/scenarios/{slug}/playbook-defaults")).json()
    resp = await client.post(f"/api/v1/scenarios/{slug}/playbooks/preview-score", json=levers)
    assert resp.status_code == 200
    result = resp.json()
    assert 0 <= result["overall"] <= 100
    by_key = {m["key"]: m for m in result["metrics"]}
    assert set(by_key) == {
        "population_coverage",
        "shelter_adequacy",
        "accessibility",
        "resource_adequacy",
    }
    assert by_key["accessibility"]["provenance"] == "synthetic"
    assert by_key["population_coverage"]["provenance"] == "real"
    assert result["uses_synthetic_data"] is True
    # raw inputs are present for defensibility
    assert "total_at_risk" in result["totals"]


async def test_create_score_list_delete_roundtrip(client: AsyncClient) -> None:
    slug = await _slug(client)
    defaults = (await client.get(f"/api/v1/scenarios/{slug}/playbook-defaults")).json()

    created = await client.post(
        f"/api/v1/scenarios/{slug}/playbooks",
        json={"name": "Integration Plan A", "levers": defaults},
    )
    assert created.status_code == 201
    pb = created.json()
    assert pb["score_result"] is not None
    overall_on_create = pb["score_result"]["overall"]
    pb_id = pb["id"]

    try:
        # Re-score is deterministic: identical overall.
        rescored = await client.post(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/score")
        assert rescored.status_code == 200
        assert rescored.json()["overall"] == overall_on_create

        # A narrower strategy (no priority regions) must score lower coverage.
        empty_levers = {**defaults, "priority_region_pcodes": [], "activated_shelter_ids": []}
        narrow = await client.post(
            f"/api/v1/scenarios/{slug}/playbooks/preview-score", json=empty_levers
        )
        narrow_cov = next(m for m in narrow.json()["metrics"] if m["key"] == "population_coverage")[
            "score"
        ]
        assert narrow_cov == 0.0

        listed = await client.get(f"/api/v1/scenarios/{slug}/playbooks")
        assert any(item["id"] == pb_id for item in listed.json())
    finally:
        deleted = await client.delete(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}")
        assert deleted.status_code == 204
