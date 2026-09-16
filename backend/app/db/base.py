"""Declarative base for all ORM models.

Domain models (incidents, shelters, assets, road closures, …) arrive in Phase 2
and will subclass ``Base``. Alembic autogenerate uses ``Base.metadata`` as the
target schema, so every future model must be imported into ``app.models`` for
migrations to see it.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# A consistent naming convention keeps Alembic migrations deterministic and
# makes constraint names predictable across environments.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all Praxis ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
