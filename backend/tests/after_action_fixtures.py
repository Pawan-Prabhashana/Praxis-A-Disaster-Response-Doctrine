"""Shared, DB-free fixtures for after-action unit tests (real 2017-shaped data)."""

from __future__ import annotations

from app.services.after_action.models import DistrictOutcome, RegionPrediction

# Praxis predicted at-risk (flood ∩ population) — Colombo highest, Ratnapura lowest.
PREDICTIONS = [
    RegionPrediction(pcode="LK11", name="Colombo", at_risk_population=367562, is_priority=True),
    RegionPrediction(pcode="LK13", name="Kalutara", at_risk_population=181445, is_priority=True),
    RegionPrediction(pcode="LK32", name="Matara", at_risk_population=135000, is_priority=True),
    RegionPrediction(pcode="LK31", name="Galle", at_risk_population=108294, is_priority=True),
    RegionPrediction(pcode="LK91", name="Ratnapura", at_risk_population=83000, is_priority=True),
]

# Real recorded 2017 impact (DesInventar) — Ratnapura most deaths, Colombo zero.
OUTCOMES = [
    DistrictOutcome(
        pcode="LK11",
        name="Colombo",
        deaths=0,
        affected=26156,
        houses_destroyed=15,
        incident_count=9,
        has_data=True,
    ),
    DistrictOutcome(
        pcode="LK13",
        name="Kalutara",
        deaths=63,
        affected=152481,
        houses_destroyed=331,
        incident_count=14,
        has_data=True,
    ),
    DistrictOutcome(
        pcode="LK32",
        name="Matara",
        deaths=40,
        affected=202666,
        houses_destroyed=799,
        incident_count=17,
        has_data=True,
    ),
    DistrictOutcome(
        pcode="LK31",
        name="Galle",
        deaths=13,
        affected=146987,
        houses_destroyed=162,
        incident_count=17,
        has_data=True,
    ),
    DistrictOutcome(
        pcode="LK91",
        name="Ratnapura",
        deaths=84,
        affected=148041,
        houses_destroyed=222,
        incident_count=23,
        has_data=True,
    ),
]
