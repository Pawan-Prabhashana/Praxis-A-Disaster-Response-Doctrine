"""playbook

Revision ID: 0003_playbook
Revises: 0002_domain_model
Create Date: 2026-09-17 13:26:21.248152
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_playbook"
down_revision: str | None = "0002_domain_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "playbook",
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("levers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("score_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
            ["scenario_id"],
            ["scenario.id"],
            name=op.f("fk_playbook_scenario_id_scenario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_playbook")),
    )
    op.create_index(op.f("ix_playbook_scenario_id"), "playbook", ["scenario_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_playbook_scenario_id"), table_name="playbook")
    op.drop_table("playbook")
