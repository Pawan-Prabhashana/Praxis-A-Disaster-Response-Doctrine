"""Tests for the system endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    """/health returns 200 and reports a healthy database connection."""
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert "version" in body


async def test_meta_returns_app_metadata(client: AsyncClient) -> None:
    """/api/v1/meta returns app identity and an (empty) scenario list."""
    response = await client.get("/api/v1/meta")

    assert response.status_code == 200
    body = response.json()
    assert body["app_name"] == "Praxis"
    assert body["scenarios"] == []
