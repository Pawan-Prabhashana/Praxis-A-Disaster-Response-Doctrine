"""ORM model registry.

Importing every model here ensures ``Base.metadata`` is fully populated (for
Alembic and for relationship resolution) whenever ``app.models`` is imported.
"""

from __future__ import annotations

from app.db.base import Base
from app.models.admin_region import AdminRegion
from app.models.brief import Brief
from app.models.data_source import DataSource
from app.models.hazard_layer import HazardLayer
from app.models.incident import Incident
from app.models.playbook import Playbook
from app.models.river import DischargeForecast, RiverPoint
from app.models.road import RoadClosure, RoadSegment
from app.models.scenario import Scenario
from app.models.shelter import Shelter
from app.models.stress_run import StressRun
from app.models.weather import WeatherReading

__all__ = [
    "Base",
    "AdminRegion",
    "Brief",
    "DataSource",
    "DischargeForecast",
    "HazardLayer",
    "Incident",
    "Playbook",
    "RiverPoint",
    "RoadClosure",
    "RoadSegment",
    "Scenario",
    "Shelter",
    "StressRun",
    "WeatherReading",
]
