"""brief

Revision ID: 0005_brief
Revises: 0004_stress_run
Create Date: 2026-09-18 09:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_brief"
down_revision: str | None = "0004_stress_run"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brief",
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("playbook_id", sa.Integer(), nullable=False),
        sa.Column("stress_run_id", sa.Integer(), nullable=True),
        sa.Column("generator", sa.String(length=20), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("facts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("guard", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["playbook_id"],
            ["playbook.id"],
            name=op.f("fk_brief_playbook_id_playbook"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenario.id"],
            name=op.f("fk_brief_scenario_id_scenario"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stress_run_id"],
            ["stress_run.id"],
            name=op.f("fk_brief_stress_run_id_stress_run"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brief")),
    )
    op.create_index(op.f("ix_brief_playbook_id"), "brief", ["playbook_id"], unique=False)
    op.create_index(op.f("ix_brief_scenario_id"), "brief", ["scenario_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_brief_scenario_id"), table_name="brief")
    op.drop_index(op.f("ix_brief_playbook_id"), table_name="brief")
    op.drop_table("brief")
