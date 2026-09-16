"""enable postgis extension

Establishes the spatial foundation for Praxis. No domain tables are created in
Phase 1 — those arrive in Phase 2 — but PostGIS must exist first so that every
subsequent migration can rely on geometry/geography column types.

Revision ID: 0001_postgis
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_postgis"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS postgis")
