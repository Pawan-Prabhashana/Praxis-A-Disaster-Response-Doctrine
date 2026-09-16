"""Synchronous SQLAlchemy engine/session for the ETL layer.

Deliberately separate from the async API engine (``app.db.session``). Bulk
geospatial loads — GeoPandas ``to_postgis``, large batched inserts — are far
simpler and faster against a blocking connection, and ETL runs as a CLI process
outside the event loop. The API never imports this module.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

sync_engine: Engine = create_engine(
    _settings.sync_database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

SyncSessionLocal: sessionmaker[Session] = sessionmaker(
    bind=sync_engine, autoflush=False, expire_on_commit=False
)


@contextmanager
def sync_session() -> Iterator[Session]:
    """Provide a transactional sync session (commit on success, rollback on error)."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
