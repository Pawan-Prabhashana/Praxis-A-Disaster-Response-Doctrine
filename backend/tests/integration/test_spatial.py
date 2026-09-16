"""PostGIS integration tests.

These require the live Docker database (``just db-up && just migrate``).
Seed-dependent assertions expect ``just data-load`` to have been run.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio

pytest.importorskip("shapely")

from geoalchemy2.shape import from_shape
from httpx import ASGITransport, AsyncClient
from shapely.geometry import Point
from sqlalchemy import text

from app.db.sync_session import sync_engine, sync_session
from app.etl.provenance import upsert_data_source
from app.main import app
from app.models.river import RiverPoint

pytestmark = pytest.mark.integration

_TEST_KEY = "__praxis_integration_pt__"
_TEST_SOURCE = "__praxis_integration_src__"


@pytest.fixture(scope="module")
def postgis() -> Iterator[None]:
    """Fail fast if PostGIS is not reachable."""
    try:
        with sync_engine.connect() as conn:
            version = conn.execute(text("SELECT PostGIS_Version()")).scalar()
            if not version:
                pytest.fail("PostGIS_Version() returned empty")
    except Exception as exc:
        pytest.fail(f"PostGIS is not reachable. Run `just db-up && just migrate`. ({exc})")
    yield


@pytest_asyncio.fixture
async def live_client(postgis: None) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def test_gist_indexes_exist(postgis: None) -> None:
    with sync_engine.connect() as conn:
        names = {
            row[0]
            for row in conn.execute(
                text(
                    """
                    SELECT indexname FROM pg_indexes
                    WHERE schemaname = 'public' AND indexdef ILIKE '%USING gist%'
                    """
                )
            )
        }
    for expected in (
        "ix_admin_region_geom_gist",
        "ix_hazard_layer_geom_gist",
        "ix_incident_geom_gist",
        "ix_shelter_geom_gist",
        "ix_road_segment_geom_gist",
        "ix_river_point_geom_gist",
    ):
        assert expected in names, f"missing GIST index {expected}"


def test_insert_and_spatial_query(postgis: None) -> None:
    """A loader insert round-trips through a PostGIS distance query."""
    with sync_session() as session:
        session.execute(text("DELETE FROM river_point WHERE key = :k"), {"k": _TEST_KEY})
        session.execute(text("DELETE FROM data_source WHERE key = :k"), {"k": _TEST_SOURCE})
        source = upsert_data_source(
            session,
            key=_TEST_SOURCE,
            name="Integration test source",
            notes="Temporary row; deleted at end of test.",
            is_synthetic=True,
        )
        session.add(
            RiverPoint(
                key=_TEST_KEY,
                name="Integration probe",
                river_name="Kalu Ganga",
                source_id=source.id,
                geom=from_shape(Point(80.384, 6.706), srid=4326),
            )
        )
        session.flush()
        within = session.execute(
            text(
                """
                SELECT ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(80.384, 6.706), 4326)::geography,
                    10
                )
                FROM river_point WHERE key = :k
                """
            ),
            {"k": _TEST_KEY},
        ).scalar()
        assert within is True
        session.execute(text("DELETE FROM river_point WHERE key = :k"), {"k": _TEST_KEY})
        session.execute(text("DELETE FROM data_source WHERE key = :k"), {"k": _TEST_SOURCE})


async def test_scenarios_and_geojson_endpoints(live_client: AsyncClient) -> None:
    listed = await live_client.get("/api/v1/scenarios")
    assert listed.status_code == 200
    scenarios = listed.json()
    assert isinstance(scenarios, list)
    assert scenarios, "Seed scenario missing; run `just data-load` first."

    slug = scenarios[0]["slug"]
    detail = await live_client.get(f"/api/v1/scenarios/{slug}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["slug"] == slug
    assert body["layers"]["admin_regions"] > 0
    assert any(not s["is_synthetic"] for s in body["sources"])

    admin = await live_client.get(f"/api/v1/scenarios/{slug}/admin-regions", params={"level": 2})
    assert admin.status_code == 200
    fc = admin.json()
    assert fc["type"] == "FeatureCollection"
    assert fc["features"], "Expected simplified district polygons"
    props = fc["features"][0]["properties"]
    assert "is_synthetic" in props
    assert "source" in props
    assert fc["features"][0]["geometry"]["type"] in {"Polygon", "MultiPolygon"}
