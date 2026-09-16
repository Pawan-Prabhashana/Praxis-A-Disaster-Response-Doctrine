"""Unit tests for P-code normalisation."""

from __future__ import annotations

from app.etl.pcodes import normalize_pcode


def test_normalize_strips_and_uppercases() -> None:
    assert normalize_pcode(" lk91 ") == "LK91"
    assert normalize_pcode("LK13") == "LK13"


def test_normalize_treats_blanks_as_missing() -> None:
    assert normalize_pcode("") is None
    assert normalize_pcode("   ") is None
    assert normalize_pcode(None) is None


def test_normalize_treats_nan_tokens_as_missing() -> None:
    assert normalize_pcode("nan") is None
    assert normalize_pcode("NaN") is None
    assert normalize_pcode("none") is None
    assert normalize_pcode(float("nan")) is None
