"""Aggregate API router mounted under the versioned prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import after_action, briefs, meta, playbooks, scenarios

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(scenarios.router)
api_router.include_router(playbooks.router)
api_router.include_router(briefs.router)
api_router.include_router(after_action.router)
