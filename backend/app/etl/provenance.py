"""Helpers for recording data provenance (``data_source`` rows)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_source import DataSource


def upsert_data_source(
    session: Session,
    *,
    key: str,
    name: str,
    url: str | None = None,
    license: str | None = None,
    notes: str | None = None,
    is_synthetic: bool = False,
) -> DataSource:
    """Insert or update a ``data_source`` row (idempotent by ``key``).

    Sets ``fetched_at`` to now so the report reflects the latest ingestion.
    Returns the persisted (flushed) row so callers can use its ``id``.
    """
    existing = session.scalar(select(DataSource).where(DataSource.key == key))
    now = datetime.now(UTC)
    if existing is None:
        source = DataSource(
            key=key,
            name=name,
            url=url,
            license=license,
            notes=notes,
            is_synthetic=is_synthetic,
            fetched_at=now,
        )
        session.add(source)
    else:
        existing.name = name
        existing.url = url
        existing.license = license
        existing.notes = notes
        existing.is_synthetic = is_synthetic
        existing.fetched_at = now
        source = existing
    session.flush()
    return source
