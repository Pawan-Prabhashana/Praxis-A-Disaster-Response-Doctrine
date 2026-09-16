"""Read APIs for scenarios and their geospatial layers."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.geojson import feature_collection
from app.db.session import get_session
from app.schemas.discharge import DischargeDay, DischargeResponse, RiverPointDischarge
from app.schemas.scenario import (
    BBox,
    LonLat,
    ScenarioDetail,
    ScenarioListItem,
    SourceInfo,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# Output simplification tolerance (degrees) per admin level — coarser for big
# national polygons, finer for local ones, to keep map payloads reasonable.
_ADMIN_TOLERANCE = {0: 0.01, 1: 0.008, 2: 0.004, 3: 0.0015, 4: 0.0005}
_HAZARD_TOLERANCE = 0.0005
_ROAD_TOLERANCE = 0.0002


class _ScenarioRef:
    """Resolved scenario identity + extent for downstream queries."""

    def __init__(self, row: Any) -> None:
        self.id: int = row.id
        self.slug: str = row.slug
        self.bbox = (row.bbox_min_lon, row.bbox_min_lat, row.bbox_max_lon, row.bbox_max_lat)


async def _resolve_scenario(slug: str, session: AsyncSession) -> _ScenarioRef:
    row = (
        await session.execute(
            text(
                """
                SELECT id, slug, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat
                FROM scenario WHERE slug = :slug
                """
            ),
            {"slug": slug},
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{slug}' not found")
    return _ScenarioRef(row)


async def scenario_ref(slug: str, session: AsyncSession = Depends(get_session)) -> _ScenarioRef:
    """Dependency: resolve the {slug} path param to a scenario, or 404."""
    return await _resolve_scenario(slug, session)


ScenarioDep = Annotated[_ScenarioRef, Depends(scenario_ref)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[ScenarioListItem], summary="List scenarios")
async def list_scenarios(session: SessionDep) -> list[ScenarioListItem]:
    rows = await session.execute(
        text(
            """
            SELECT id, slug, name, hazard_type, status, event_date
            FROM scenario ORDER BY event_date DESC NULLS LAST, name
            """
        )
    )
    return [ScenarioListItem(**r._mapping) for r in rows]


@router.get("/{slug}", response_model=ScenarioDetail, summary="Scenario detail")
async def get_scenario(scenario: ScenarioDep, session: SessionDep) -> ScenarioDetail:
    detail = (
        await session.execute(
            text(
                """
                SELECT s.id, s.slug, s.name, s.hazard_type, s.status, s.event_date,
                       s.description, s.bbox_min_lon, s.bbox_min_lat, s.bbox_max_lon,
                       s.bbox_max_lat, ST_X(s.center) AS clon, ST_Y(s.center) AS clat
                FROM scenario s WHERE s.id = :sid
                """
            ),
            {"sid": scenario.id},
        )
    ).one()

    counts = (
        await session.execute(
            text(
                """
                SELECT
                    (SELECT count(*) FROM admin_region) AS admin_regions,
                    (SELECT count(*) FROM hazard_layer
                       WHERE scenario_id = :sid OR scenario_id IS NULL) AS hazard_layers,
                    (SELECT count(*) FROM incident WHERE scenario_id = :sid) AS incidents,
                    (SELECT count(*) FROM shelter) AS shelters,
                    (SELECT count(*) FROM road_segment) AS roads,
                    (SELECT count(*) FROM road_closure WHERE scenario_id = :sid) AS road_closures,
                    (SELECT count(*) FROM river_point) AS river_points,
                    (SELECT count(*) FROM discharge_forecast
                       WHERE scenario_id = :sid) AS discharge_forecasts,
                    (SELECT count(*) FROM weather_reading) AS weather_readings
                """
            ),
            {"sid": scenario.id},
        )
    ).one()

    sources = await session.execute(
        text("SELECT key, name, license, is_synthetic FROM data_source ORDER BY is_synthetic, key")
    )

    m = detail._mapping
    bbox = (
        BBox(
            min_lon=m["bbox_min_lon"],
            min_lat=m["bbox_min_lat"],
            max_lon=m["bbox_max_lon"],
            max_lat=m["bbox_max_lat"],
        )
        if m["bbox_min_lon"] is not None
        else None
    )
    center = LonLat(lon=m["clon"], lat=m["clat"]) if m["clon"] is not None else None
    return ScenarioDetail(
        id=m["id"],
        slug=m["slug"],
        name=m["name"],
        hazard_type=m["hazard_type"],
        status=m["status"],
        event_date=m["event_date"],
        description=m["description"],
        bbox=bbox,
        center=center,
        layers=dict(counts._mapping),
        sources=[SourceInfo(**r._mapping) for r in sources],
    )


@router.get("/{slug}/admin-regions", summary="Admin regions (GeoJSON)")
async def admin_regions(
    scenario: ScenarioDep,
    session: SessionDep,
    level: int = Query(2, ge=0, le=4, description="COD-AB level (0 country … 4 GN division)."),
) -> dict[str, Any]:
    inner = """
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(a.geom, :tol))::jsonb,
            'properties', jsonb_build_object(
                'id', a.id, 'pcode', a.pcode, 'level', a.level,
                'name_en', a.name_en, 'name_si', a.name_si, 'name_ta', a.name_ta,
                'population', a.population, 'source', ds.name, 'is_synthetic', ds.is_synthetic
            )
        ) AS feature
        FROM admin_region a
        JOIN data_source ds ON ds.id = a.source_id
        WHERE a.level = :level
          AND a.geom && ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326)
    """
    return await feature_collection(
        session,
        inner,
        {
            "tol": _ADMIN_TOLERANCE.get(level, 0.003),
            "level": level,
            "minx": scenario.bbox[0],
            "miny": scenario.bbox[1],
            "maxx": scenario.bbox[2],
            "maxy": scenario.bbox[3],
        },
    )


@router.get("/{slug}/hazard-layers", summary="Hazard layers (GeoJSON)")
async def hazard_layers(
    scenario: ScenarioDep,
    session: SessionDep,
    type: str | None = Query(None, description="Filter by layer_type (e.g. flood_extent)."),
) -> dict[str, Any]:
    inner = """
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(h.geom, :tol))::jsonb,
            'properties', jsonb_build_object(
                'id', h.id, 'layer_type', h.layer_type, 'name', h.name,
                'severity_class', h.severity_class, 'severity_label', h.severity_label,
                'is_synthetic', h.is_synthetic, 'source', ds.name
            )
        ) AS feature
        FROM hazard_layer h
        JOIN data_source ds ON ds.id = h.source_id
        WHERE (h.scenario_id = :sid OR h.scenario_id IS NULL)
          AND (CAST(:type AS text) IS NULL OR h.layer_type = CAST(:type AS text))
    """
    return await feature_collection(
        session, inner, {"tol": _HAZARD_TOLERANCE, "sid": scenario.id, "type": type}
    )


@router.get("/{slug}/shelters", summary="Candidate shelters (GeoJSON)")
async def shelters(scenario: ScenarioDep, session: SessionDep) -> dict[str, Any]:
    inner = """
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(s.geom)::jsonb,
            'properties', jsonb_build_object(
                'id', s.id, 'name', s.name, 'kind', s.kind, 'capacity', s.capacity,
                'is_synthetic', s.is_synthetic, 'source', ds.name,
                'note', 'Candidate shelter derived from OSM — not an official registry.'
            )
        ) AS feature
        FROM shelter s
        JOIN data_source ds ON ds.id = s.source_id
        WHERE s.geom && ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326)
    """
    return await feature_collection(
        session,
        inner,
        {
            "minx": scenario.bbox[0],
            "miny": scenario.bbox[1],
            "maxx": scenario.bbox[2],
            "maxy": scenario.bbox[3],
        },
    )


@router.get("/{slug}/incidents", summary="Historical incidents (GeoJSON)")
async def incidents(scenario: ScenarioDep, session: SessionDep) -> dict[str, Any]:
    inner = """
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(i.geom)::jsonb,
            'properties', jsonb_build_object(
                'id', i.id, 'type', i.type, 'severity', i.severity,
                'occurred_at', i.occurred_at, 'description', i.description,
                'is_synthetic', i.is_synthetic, 'source', ds.name
            )
        ) AS feature
        FROM incident i
        JOIN data_source ds ON ds.id = i.source_id
        WHERE i.scenario_id = :sid
    """
    return await feature_collection(session, inner, {"sid": scenario.id})


@router.get("/{slug}/roads", summary="Roads (GeoJSON)")
async def roads(
    scenario: ScenarioDep,
    session: SessionDep,
    closed: bool | None = Query(None, description="true=only closed, false=only open."),
) -> dict[str, Any]:
    inner = """
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(r.geom, :tol))::jsonb,
            'properties', jsonb_build_object(
                'id', r.id, 'name', r.name, 'road_class', r.road_class,
                'closed', (rc.id IS NOT NULL),
                'closure_reason', rc.reason,
                'is_synthetic', ds.is_synthetic,
                'closure_is_synthetic', rc.is_synthetic,
                'source', ds.name
            )
        ) AS feature
        FROM road_segment r
        JOIN data_source ds ON ds.id = r.source_id
        LEFT JOIN road_closure rc
          ON rc.road_segment_id = r.id AND rc.scenario_id = :sid
        WHERE r.geom && ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326)
          AND (CAST(:closed AS boolean) IS NULL
               OR (CAST(:closed AS boolean) = true AND rc.id IS NOT NULL)
               OR (CAST(:closed AS boolean) = false AND rc.id IS NULL))
    """
    return await feature_collection(
        session,
        inner,
        {
            "tol": _ROAD_TOLERANCE,
            "sid": scenario.id,
            "closed": closed,
            "minx": scenario.bbox[0],
            "miny": scenario.bbox[1],
            "maxx": scenario.bbox[2],
            "maxy": scenario.bbox[3],
        },
    )


@router.get("/{slug}/rivers", summary="River points (GeoJSON)")
async def rivers(scenario: ScenarioDep, session: SessionDep) -> dict[str, Any]:
    inner = """
        SELECT jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(rp.geom)::jsonb,
            'properties', jsonb_build_object(
                'id', rp.id, 'key', rp.key, 'name', rp.name,
                'river_name', rp.river_name,
                'is_synthetic', ds.is_synthetic, 'source', ds.name
            )
        ) AS feature
        FROM river_point rp
        JOIN data_source ds ON ds.id = rp.source_id
    """
    return await feature_collection(session, inner, {})


@router.get("/{slug}/discharge", response_model=DischargeResponse, summary="River discharge")
async def discharge(
    scenario: ScenarioDep,
    session: SessionDep,
    river_point_id: int | None = Query(None, description="Restrict to one river point."),
) -> DischargeResponse:
    rows = await session.execute(
        text(
            """
            SELECT rp.id AS river_point_id, rp.key, rp.name, rp.river_name,
                   ST_X(rp.geom) AS lon, ST_Y(rp.geom) AS lat,
                   ds.name AS source, ds.is_synthetic,
                   df.valid_date, df.discharge_mean, df.discharge_median,
                   df.discharge_p25, df.discharge_p75, df.discharge_min, df.discharge_max
            FROM discharge_forecast df
            JOIN river_point rp ON rp.id = df.river_point_id
            JOIN data_source ds ON ds.id = df.source_id
            WHERE df.scenario_id = :sid
              AND (CAST(:rpid AS integer) IS NULL OR rp.id = CAST(:rpid AS integer))
            ORDER BY rp.name, df.valid_date
            """
        ),
        {"sid": scenario.id, "rpid": river_point_id},
    )

    points: dict[int, RiverPointDischarge] = {}
    for r in rows:
        rid = r.river_point_id
        if rid not in points:
            points[rid] = RiverPointDischarge(
                river_point_id=rid,
                key=r.key,
                name=r.name,
                river_name=r.river_name,
                lon=r.lon,
                lat=r.lat,
                source=r.source,
                is_synthetic=r.is_synthetic,
                series=[],
            )
        points[rid].series.append(
            DischargeDay(
                valid_date=r.valid_date,
                mean=r.discharge_mean,
                median=r.discharge_median,
                p25=r.discharge_p25,
                p75=r.discharge_p75,
                min=r.discharge_min,
                max=r.discharge_max,
            )
        )

    return DischargeResponse(scenario_slug=scenario.slug, points=list(points.values()))
