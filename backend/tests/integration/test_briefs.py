"""Brief API integration tests (require live PostGIS + seed data).

Runs entirely without an LLM key: the brief must generate via the template path,
persist, be fetchable, and export to HTML + a real PDF.
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
    # Force the LLM off regardless of any local .env so tests never call a real
    # API and always exercise the deterministic template path.
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
        json={"name": "Brief Integration Plan", "levers": defaults},
    )
    assert created.status_code == 201
    return int(created.json()["id"])


async def test_generate_persist_fetch_export(client: AsyncClient) -> None:
    slug = await _slug(client)
    pb_id = await _make_playbook(client, slug)
    try:
        # Generate a brief with NO LLM key -> deterministic template path.
        gen = await client.post(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/brief", json={})
        assert gen.status_code == 201
        brief = gen.json()
        assert brief["generator"] == "template"
        assert brief["guard"]["ok"] is True
        keys = [s["key"] for s in brief["content"]["sections"]]
        assert keys == ["situation", "strategy", "performance", "tasking", "risks", "provenance"]
        # Facts snapshot is stored and carries the honesty flag.
        assert brief["facts"]["uses_synthetic_data"] is True
        brief_id = brief["id"]

        # List + fetch.
        listed = await client.get(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/briefs")
        assert any(b["id"] == brief_id for b in listed.json())
        fetched = await client.get(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/briefs/{brief_id}")
        assert fetched.status_code == 200

        # HTML export.
        html = await client.get(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/briefs/{brief_id}/export.html"
        )
        assert html.status_code == 200
        assert "<html" in html.text.lower()
        assert "validated against source" in html.text

        # PDF export is a real PDF.
        pdf = await client.get(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/briefs/{brief_id}/export.pdf"
        )
        assert pdf.status_code == 200
        assert pdf.headers["content-type"] == "application/pdf"
        assert pdf.content[:5] == b"%PDF-"
    finally:
        await client.delete(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}")


async def test_brief_with_stress_run_carries_robustness(client: AsyncClient) -> None:
    slug = await _slug(client)
    pb_id = await _make_playbook(client, slug)
    try:
        run = await client.post(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/stress-test",
            json={"n_iterations": 200, "seed": 7},
        )
        assert run.status_code == 201
        run_id = run.json()["id"]

        gen = await client.post(
            f"/api/v1/scenarios/{slug}/playbooks/{pb_id}/brief",
            json={"stress_run_id": run_id},
        )
        assert gen.status_code == 201
        brief = gen.json()
        assert brief["stress_run_id"] == run_id
        assert brief["facts"]["robustness"] is not None
        assert brief["facts"]["robustness"]["seed"] == 7
    finally:
        await client.delete(f"/api/v1/scenarios/{slug}/playbooks/{pb_id}")
