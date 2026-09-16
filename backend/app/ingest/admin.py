"""Ingest COD-AB administrative boundaries + COD-PS population from HDX."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from sqlalchemy import text

from app.core.logging import get_logger
from app.db.sync_session import sync_engine, sync_session
from app.etl import seed_manifest as m
from app.etl.geo import force_multipolygon_column, to_wgs84
from app.etl.hdx import get_dataset
from app.etl.http import download_file
from app.etl.pcodes import normalize_pcode
from app.etl.provenance import upsert_data_source

_log = get_logger("praxis.ingest.admin")

COD_AB_DATASET = "cod-ab-lka"
COD_PS_DATASET = "cod-ps-lka"
_MAX_LEVEL = 4


def _clean_str(series: pd.Series) -> pd.Series:
    """Normalise a text column: strip, treat blank/'nan' as missing (pd.NA)."""
    out = series.astype("string").str.strip()
    return out.mask(out.isna() | (out == "") | (out.str.lower() == "nan"))


def _load_level(zip_path: str, level: int, source_id: int) -> gpd.GeoDataFrame:
    """Build a normalised admin GeoDataFrame for one COD-AB level."""
    raw = gpd.read_file(f"/vsizip/{zip_path}/lka_admin{level}.shp")
    if level == _MAX_LEVEL:
        # GN divisions only for the seed districts (keeps the load focused).
        raw = raw[raw["adm2_pcode"].isin(m.SEED_DISTRICT_PCODES)]

    pcode = raw[f"adm{level}_pcode"].map(normalize_pcode)
    name_en = _clean_str(raw[f"adm{level}_name"])
    # A handful of GN divisions have no name; fall back to the P-code so the
    # NOT NULL name is preserved and the row is still identifiable.
    name_en = name_en.fillna(pcode)
    parent = raw[f"adm{level - 1}_pcode"].map(normalize_pcode) if level > 0 else None

    frame = gpd.GeoDataFrame(
        {
            "level": level,
            "pcode": pcode,
            "parent_pcode": parent,
            "name_en": name_en,
            "source_id": source_id,
            "geometry": raw.geometry,
        },
        geometry="geometry",
        crs=raw.crs,
    )
    frame = frame[frame["pcode"].notna()]
    frame = force_multipolygon_column(to_wgs84(frame))
    frame = frame.drop_duplicates(subset="pcode").reset_index(drop=True)
    return frame.rename_geometry("geom")


def _apply_population(csv_path: str, level: int) -> int:
    """Update population + Sinhala/Tamil names from a COD-PS CSV. Returns rows touched."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    pcode_col = f"ADM{level}_PCODE"
    si_col, ta_col = f"ADM{level}_NAME_SI", f"ADM{level}_NAME_TA"
    updates = [
        {
            "pcode": normalize_pcode(r[pcode_col]),
            "pop": int(r["T_TL"]) if pd.notna(r["T_TL"]) else None,
            "si": str(r[si_col]) if si_col in df.columns and pd.notna(r.get(si_col)) else None,
            "ta": str(r[ta_col]) if ta_col in df.columns and pd.notna(r.get(ta_col)) else None,
        }
        for _, r in df.iterrows()
        if normalize_pcode(r[pcode_col]) is not None
    ]
    with sync_session() as session:
        session.execute(
            text(
                """
                UPDATE admin_region
                SET population = :pop,
                    name_si = COALESCE(:si, name_si),
                    name_ta = COALESCE(:ta, name_ta)
                WHERE pcode = :pcode
                """
            ),
            updates,
        )
    return len(updates)


def run_admin(*, force: bool = False) -> dict[str, int]:
    """Ingest admin boundaries (levels 0-4) and population. Idempotent."""
    ab = get_dataset(COD_AB_DATASET)
    ab_res = ab.find(name_contains="admin_boundaries", fmt="SHP")
    ab_zip = download_file(ab_res.url, "lka_admin_boundaries.shp.zip", force=force)

    ps = get_dataset(COD_PS_DATASET)

    with sync_session() as session:
        source = upsert_data_source(
            session,
            key="hdx-cod-ab-lka",
            name=ab.title,
            url=f"https://data.humdata.org/dataset/{COD_AB_DATASET}",
            license=ab.license,
            notes="COD-AB admin boundaries; GN divisions (adm4) scoped to seed districts.",
        )
        source_id = source.id

    # Delete existing admin rows for this source, then append level-by-level so
    # the self-referential parent_pcode FK is always satisfied (parents first).
    with sync_engine.begin() as conn:
        conn.execute(text("DELETE FROM admin_region WHERE source_id = :sid"), {"sid": source_id})

    counts: dict[str, int] = {}
    for level in range(_MAX_LEVEL + 1):
        frame = _load_level(str(ab_zip), level, source_id)
        frame.to_postgis("admin_region", sync_engine, if_exists="append", index=False)
        counts[f"admin_level_{level}"] = len(frame)
        _log.info("admin.level_loaded", level=level, rows=len(frame))

    # Record COD-PS provenance, then apply population + SI/TA names for the
    # levels COD-PS publishes (0-2). Population is an attribute update on the
    # COD-AB rows; COD-PS is tracked as its own source for the ledger.
    with sync_session() as session:
        upsert_data_source(
            session,
            key="hdx-cod-ps-lka",
            name=ps.title,
            url=f"https://data.humdata.org/dataset/{COD_PS_DATASET}",
            license=ps.license,
            notes="COD-PS population (2023) joined onto admin regions by P-code.",
        )
    for level in range(3):
        res = ps.find(name_contains=f"adm{level}_2023", fmt="CSV")
        csv_path = download_file(res.url, f"lka_admpop_adm{level}_2023.csv", force=force)
        counts[f"population_level_{level}"] = _apply_population(str(csv_path), level)
    return counts
