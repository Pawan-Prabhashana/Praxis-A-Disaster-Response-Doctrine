"""Aggregate API router mounted under the versioned prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import meta

api_router = APIRouter()
api_router.include_router(meta.router)
