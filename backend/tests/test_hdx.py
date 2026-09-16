"""Unit tests for HDX resource matching."""

from __future__ import annotations

import pytest

from app.etl.hdx import HdxDataset, HdxResource
from app.etl.http import FetchError


def _dataset() -> HdxDataset:
    return HdxDataset(
        dataset_id="cod-ab-lka",
        title="Sri Lanka admin boundaries",
        license="Creative Commons Attribution",
        resources=[
            HdxResource("lka_admin_boundaries.shp.zip", "SHP", "https://example.test/ab.zip"),
            HdxResource("lka_admpop_adm2_2023.csv", "CSV", "https://example.test/pop.csv"),
        ],
    )


def test_find_by_name_and_format() -> None:
    res = _dataset().find(name_contains="admin_boundaries", fmt="SHP")
    assert res.url.endswith("ab.zip")


def test_find_fails_loudly_when_missing() -> None:
    with pytest.raises(FetchError, match="No HDX resource"):
        _dataset().find(name_contains="unosat", fmt="GeoJSON")
