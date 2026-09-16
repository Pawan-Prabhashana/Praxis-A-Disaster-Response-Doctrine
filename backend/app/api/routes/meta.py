"""Application metadata endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.meta import MetaResponse

router = APIRouter(tags=["system"])


@router.get("/meta", response_model=MetaResponse, summary="Application metadata")
async def meta() -> MetaResponse:
    """Return app identity.

    The scenario catalogue lives at ``GET /api/v1/scenarios`` (Phase 2). The
    ``scenarios`` field here stays empty so the original meta contract is
    unchanged.
    """
    settings = get_settings()
    return MetaResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        scenarios=[],
    )
