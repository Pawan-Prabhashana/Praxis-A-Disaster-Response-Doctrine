"""Praxis API application factory.

Assembles the FastAPI app: configuration, structured logging, CORS, the
request-context middleware, and the system routes (``/health`` and the
versioned ``/api/v1`` surface).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes import health
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: log a clean startup/shutdown boundary."""
    settings = get_settings()
    log = get_logger("praxis.lifespan")
    log.info(
        "app.startup",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    await _warm_scoring_cache(log)
    yield
    log.info("app.shutdown", app=settings.app_name)


async def _warm_scoring_cache(log) -> None:
    """Best-effort warm of the (heavy, one-time) per-scenario region facts so the
    first Playbook Studio request is instant. Never blocks startup on failure."""
    try:
        from sqlalchemy import text

        from app.db.session import SessionLocal
        from app.services.scoring.gather import _region_facts

        async with SessionLocal() as session:
            ids = (await session.execute(text("SELECT id FROM scenario"))).scalars().all()
            for scenario_id in ids:
                await _region_facts(session, int(scenario_id))
        log.info("scoring.cache_warmed", scenarios=len(ids))
    except Exception as exc:
        log.warning("scoring.cache_warm_failed", error=str(exc))


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(json_logs=settings.is_production)

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        summary="Disaster Response Doctrine & Command Platform for Sri Lanka.",
        lifespan=lifespan,
    )

    # CORS for the browser client (Vite dev server by default).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)

    # System routes: /health at the root, everything else under /api/v1.
    app.include_router(health.router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
