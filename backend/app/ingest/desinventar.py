"""Ingest historical flood/landslide loss records from DesInventar Sri Lanka.

Source: the official DesInventar Sri Lanka database export (national disaster
loss inventory). The export's XML is large, so we stream it with iterparse and
keep only flood/landslide cards in the seed districts. Each card is geolocated
by its own lat/lon when present, otherwise by the centroid of its DS division
(from the export's bundled ``dsdivi`` shapefile).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime

import geopandas as gpd
from shapely.geometry import Point

from app.core.logging import get_logger
from app.db.sync_session import sync_engine, sync_session
from app.etl.geo import to_wgs84
from app.etl.http import download_file
from app.etl.loading import replace_geo_by_source
from app.etl.provenance import upsert_data_source
from app.ingest.scenario import require_scenario

_log = get_logger("praxis.ingest.desinventar")

EXPORT_URL = "https://www.desinventar.net/DesInventar/download/DI_export_lka.zip"
SEED_DISTRICT_NAMES = {"Ratnapura", "Kalutara", "Galle", "Matara", "Colombo"}
_HAZARD_KEYWORDS = ("flood", "landslide", "mass movement", "cyclone", "storm")


def _ds_centroids(zip_path: str) -> dict[str, tuple[float, float, str]]:
    """Map DesInventar DS-division code → (lon, lat, district_name)."""
    gdf = to_wgs84(gpd.read_file(f"/vsizip/{zip_path}/dsdivi.shp"))
    gdf["centroid"] = gdf.geometry.representative_point()
    out: dict[str, tuple[float, float, str]] = {}
    for _, row in gdf.iterrows():
        code = str(row["ds_code"])
        out[code] = (row["centroid"].x, row["centroid"].y, str(row.get("DISTRICT_N") or ""))
    return out


def _to_int(value: str | None) -> int:
    try:
        return int(float(value)) if value not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def _occurred_at(card: dict) -> datetime | None:
    year = _to_int(card.get("fechano"))
    if year <= 0:
        return None
    month = min(max(_to_int(card.get("fechames")) or 1, 1), 12)
    day = min(max(_to_int(card.get("fechadia")) or 1, 1), 28)
    return datetime(year, month, day, tzinfo=UTC)


def _severity(deaths: int, affected: int) -> str:
    if deaths > 0:
        return "fatal"
    if affected >= 1000:
        return "major"
    if affected > 0:
        return "significant"
    return "minor"


def _iter_cards(zip_path: str):
    """Yield DesInventar cards (as field dicts) by streaming the export XML."""
    fields = (
        "serial", "level1", "level2", "name1", "name2", "evento", "lugar",
        "fechano", "fechames", "fechadia", "muertos", "afectados", "vivdest",
        "latitude", "longitude",
    )  # fmt: skip
    with zipfile.ZipFile(zip_path) as zf, zf.open("DI_export_lka.xml") as fh:
        for _, el in ET.iterparse(fh, events=("end",)):
            if el.tag != "TR" or el.find("evento") is None:
                continue
            card = {f: (el.findtext(f) or "").strip() for f in fields}
            el.clear()
            if card["serial"]:
                yield card


def run_desinventar(*, force: bool = False) -> dict[str, int]:
    """Load historical flood/landslide incidents for the seed districts."""
    zip_path = download_file(EXPORT_URL, "DI_export_lka.zip", force=force, timeout=600.0)
    centroids = _ds_centroids(str(zip_path))

    with sync_session() as session:
        scenario = require_scenario(session)
        scenario_id = scenario.id
        source = upsert_data_source(
            session,
            key="desinventar-lka",
            name="DesInventar Sri Lanka — historical disaster loss database",
            url="https://www.desinventar.net/DesInventar/profiletab.jsp?countrycode=lka",
            license="DesInventar (UNDRR) — see database terms",
            notes="Historical flood/landslide loss records for the seed districts.",
        )
        source_id = source.id

    records: list[dict] = []
    scanned = 0
    for card in _iter_cards(str(zip_path)):
        scanned += 1
        event = card["evento"].lower()
        if not any(k in event for k in _HAZARD_KEYWORDS):
            continue

        lon = lat = None
        district = ""
        centroid = centroids.get(card["level2"])
        if centroid:
            lon, lat, district = centroid
        # Prefer an explicit card coordinate when present and plausible.
        try:
            clat, clon = float(card["latitude"]), float(card["longitude"])
            if 5 <= clat <= 10 and 79 <= clon <= 82:
                lon, lat = clon, clat
        except (TypeError, ValueError):
            pass
        if lon is None or lat is None:
            continue
        if district and district not in SEED_DISTRICT_NAMES:
            continue

        deaths, affected = _to_int(card["muertos"]), _to_int(card["afectados"])
        occurred = _occurred_at(card)
        records.append(
            {
                "external_id": f"desinventar:{card['serial']}",
                "type": card["evento"] or "Unknown",
                "severity": _severity(deaths, affected),
                "description": (
                    f"{card['evento'].title()} at {card['lugar'] or district}. "
                    f"Deaths: {deaths}, affected: {affected}, houses destroyed: "
                    f"{_to_int(card['vivdest'])}."
                ),
                "occurred_at": occurred,
                "admin_region_id": None,
                "scenario_id": scenario_id,
                "source_id": source_id,
                "is_synthetic": False,
                "geometry": Point(lon, lat),
            }
        )

    if not records:
        raise RuntimeError("DesInventar parse produced no matching incidents")

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    rows = replace_geo_by_source(gdf, table="incident", source_id=source_id)

    # Link incidents to their district (admin level 2) by point-in-polygon.
    _link_incidents_to_admin(source_id)
    _log.info("desinventar.done", scanned=scanned, loaded=rows)
    return {"historical_incidents": rows, "cards_scanned": scanned}


def _link_incidents_to_admin(source_id: int) -> None:
    from sqlalchemy import text

    with sync_engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE incident i
                SET admin_region_id = a.id
                FROM admin_region a
                WHERE a.level = 2
                  AND i.source_id = :sid
                  AND ST_Contains(a.geom, i.geom)
                """
            ),
            {"sid": source_id},
        )
