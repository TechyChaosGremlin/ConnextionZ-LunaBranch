"""Add block and mute relationships used by feed safety filtering.

Revision ID: 002
Revises: 001
Create Date: 2026-08-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name, owner_column, target_column, constraint_name in (
        ("user_blocks", "blocker_id", "blocked_id", "uq_user_block_pair"),
        ("user_mutes", "muter_id", "muted_id", "uq_user_mute_pair"),
    ):
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(owner_column, postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(target_column, postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint([owner_column], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint([target_column], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint(owner_column, target_column, name=constraint_name),
        )
        op.create_index(f"ix_{table_name}_{owner_column}", table_name, [owner_column])
        op.create_index(f"ix_{table_name}_{target_column}", table_name, [target_column])


def downgrade() -> None:
    for table_name, owner_column, target_column in (
        ("user_mutes", "muter_id", "muted_id"),
        ("user_blocks", "blocker_id", "blocked_id"),
    ):
        op.drop_index(f"ix_{table_name}_{target_column}", table_name=table_name)
        op.drop_index(f"ix_{table_name}_{owner_column}", table_name=table_name)
        op.drop_table(table_name)