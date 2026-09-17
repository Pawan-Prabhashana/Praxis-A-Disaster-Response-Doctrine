"""stress run

Revision ID: 0004_stress_run
Revises: 0003_playbook
Create Date: 2026-09-17 19:02:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_stress_run"
down_revision: str | None = "0003_playbook"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stress_run",
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("playbook_id", sa.Integer(), nullable=False),
        sa.Column("n_iterations", sa.Integer(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            name=op.f("fk_stress_run_playbook_id_playbook"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenario.id"],
            name=op.f("fk_stress_run_scenario_id_scenario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stress_run")),
    )
    op.create_index(op.f("ix_stress_run_playbook_id"), "stress_run", ["playbook_id"], unique=False)
    op.create_index(op.f("ix_stress_run_scenario_id"), "stress_run", ["scenario_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stress_run_scenario_id"), table_name="stress_run")
    op.drop_index(op.f("ix_stress_run_playbook_id"), table_name="stress_run")
    op.drop_table("stress_run")
