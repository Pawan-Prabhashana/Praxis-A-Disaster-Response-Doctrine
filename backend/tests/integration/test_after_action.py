"""After-action API integration tests (require live PostGIS + seed data).

Keyless: lessons must come from the deterministic template. Exercises the real
DesInventar recorded-outcomes aggregation and the build->persist->fetch flow.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import Settings, get_settings
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
    app.dependency_overrides[get_settings] = lambda: Settings(llm_enabled=False, llm_api_key=None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_settings, None)
    await engine.dispose()


async def _slug(client: AsyncClient) -> str:
    scenarios = (await client.get("/api/v1/scenarios")).json()
    assert scenarios, "Seed scenario missing; run `just data-load`."
    return scenarios[0]["slug"]


async def _make_playbook(client: AsyncClient, slug: str) -> int:
    defaults = (await client.get(f"/api/v1/scenarios/{slug}/playbook-defaults")).json()
    created = await client.post(
        f"/api/v1/scenarios/{slug}/playbooks",
        json={"name": "After-action Plan", "levers": defaults},
    )
    assert created.status_code == 201
    return int(created.json()["id"])


async def test_recorded_outcomes_are_real_and_labelled(client: AsyncClient) -> None:
    slug = await _slug(client)
    resp = await client.get(f"/api/v1/scenarios/{slug}/recorded-outcomes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_synthetic"] is False
    assert "not the outcome of executing" in body["framing"].lower()
    # Real 2017 signal: Ratnapura recorded deaths, and some district has data.
    by = {d["name"]: d for d in body["districts"]}
    assert body["totals"]["districts_with_data"] >= 1
    if "Ratnapura" in by and by["Ratnapura"]["has_data"]:
        assert by["Ratnapura"]["deaths"] > 0


async def test_build_persist_fetch_after_action(client: AsyncClient) -> None:
    slug = await _slug(client)
    pb_id = await _make_playbook(client, slug)
    try:
        gen = await client.post(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/after-action", json={})
        assert gen.status_code == 201
        aa = gen.json()
        assert aa["generator"] == "template"  # keyless
        assert aa["event_year"] == 2017
        assert aa["result"]["recorded_is_real"] is True
        assert aa["lessons"]["guard"]["ok"] is True
        assert any(le["key"] == "alignment" for le in aa["lessons"]["lessons"])
        aa_id = aa["id"]

        listed = await client.get(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/after-actions")
        assert any(item["id"] == aa_id for item in listed.json())
        fetched = await client.get(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/after-actions/{aa_id}"
        )
        assert fetched.status_code == 200
        assert fetched.json()["result"]["alignment"]["label"] in {
            "strong",
            "moderate",
            "weak",
            "inverted",
        }
    finally:
        await client.delete(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}")
