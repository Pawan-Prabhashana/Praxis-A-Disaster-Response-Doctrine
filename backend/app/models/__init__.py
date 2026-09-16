"""ORM model registry.

Domain models arrive in Phase 2. Import each model module here so that
``Base.metadata`` is fully populated for Alembic autogenerate, e.g.::

    from app.models.incident import Incident  # noqa: F401

For now there are no domain tables — only the PostGIS extension, enabled by the
initial migration.
"""

from __future__ import annotations

from app.db.base import Base

__all__ = ["Base"]
