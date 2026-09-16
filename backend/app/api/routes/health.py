"""Health / readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_session
from app.schemas.health import ComponentStatus, HealthResponse

router = APIRouter(tags=["system"])
_log = get_logger("praxis.health")


async def _check_database(session: AsyncSession) -> ComponentStatus:
    """Run a trivial query to confirm real database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        _log.warning("health.db_check_failed", error=str(exc))
        return ComponentStatus.ERROR
    return ComponentStatus.OK


@router.get("/health", response_model=HealthResponse, summary="Service health")
async def health(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    """Return service liveness plus a live database connectivity probe.

    Always responds ``200`` so orchestrators can distinguish "reachable but
    degraded" from "unreachable"; inspect the ``db`` field for readiness.
    """
    settings = get_settings()
    db_status = await _check_database(session)
    overall = ComponentStatus.OK if db_status is ComponentStatus.OK else ComponentStatus.ERROR
    return HealthResponse(
        status=overall,
        db=db_status,
        version=settings.app_version,
        environment=settings.environment,
    )
