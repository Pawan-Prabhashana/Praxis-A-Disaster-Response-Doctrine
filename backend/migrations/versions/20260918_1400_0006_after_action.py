"""after action

Revision ID: 0006_after_action
Revises: 0005_brief
Create Date: 2026-09-18 14:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006_after_action"
down_revision: str | None = "0005_brief"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "after_action",
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("playbook_id", sa.Integer(), nullable=False),
        sa.Column("brief_id", sa.Integer(), nullable=True),
        sa.Column("stress_run_id", sa.Integer(), nullable=True),
        sa.Column("event_year", sa.Integer(), nullable=True),
        sa.Column("generator", sa.String(length=20), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("lessons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            ["brief_id"],
            ["brief.id"],
            name=op.f("fk_after_action_brief_id_brief"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["playbook_id"],
            ["playbook.id"],
            name=op.f("fk_after_action_playbook_id_playbook"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenario.id"],
            name=op.f("fk_after_action_scenario_id_scenario"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stress_run_id"],
            ["stress_run.id"],
            name=op.f("fk_after_action_stress_run_id_stress_run"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_after_action")),
    )
    op.create_index(
        op.f("ix_after_action_playbook_id"), "after_action", ["playbook_id"], unique=False
    )
    op.create_index(
        op.f("ix_after_action_scenario_id"), "after_action", ["scenario_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_after_action_scenario_id"), table_name="after_action")
    op.drop_index(op.f("ix_after_action_playbook_id"), table_name="after_action")
    op.drop_table("after_action")
