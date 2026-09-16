"""Application metadata endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.meta import MetaResponse

router = APIRouter(tags=["system"])


@router.get("/meta", response_model=MetaResponse, summary="Application metadata")
async def meta() -> MetaResponse:
    """Return app identity and the (currently empty) scenario catalogue.

    Scenarios are seeded in Phase 2; the empty list keeps the frontend
    scenario-selector contract stable in the meantime.
    """
    settings = get_settings()
    return MetaResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        scenarios=[],
    )
