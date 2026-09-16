"""Alembic migration environment (async).

Runs migrations against the same async engine and metadata the application
uses, sourcing the database URL from application settings so there is a single
source of truth for connection details.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

# Import models so that ``Base.metadata`` is fully populated for autogenerate.
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the runtime database URL from settings.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Keep autogenerate focused on Praxis-owned tables.

    PostGIS ships system tables (``spatial_ref_sys`` and the ``tiger`` /
    ``topology`` schema tables) that are not part of our metadata. Without this
    filter, autogenerate would propose dropping them. We ignore any reflected
    table that is not defined in ``target_metadata``.
    """
    return not (type_ == "table" and reflected and name not in target_metadata.tables)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI connection)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode against the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
