"""Schemas for the health endpoint."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ComponentStatus(str, Enum):
    """Status of an individual dependency."""

    OK = "ok"
    ERROR = "error"


class HealthResponse(BaseModel):
    """Liveness + dependency readiness report."""

    status: ComponentStatus = Field(
        description="Overall service status; 'ok' only when every component is healthy."
    )
    db: ComponentStatus = Field(description="Database connectivity check result.")
    version: str = Field(description="Running application version.")
    environment: str = Field(description="Deployment environment name.")
