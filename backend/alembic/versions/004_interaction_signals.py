"""Unified recommendation-ready engagement signal log (interaction_signals).

Revision ID: 004
Revises: 003
Create Date: 2026-08-30 00:00:00.000000
"""

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


SIGNAL_TYPES = (
    "view",
    "watch_duration",
    "completion",
    "rewatch",
    "like",
    "unlike",
    "save",
    "unsave",
    "share",
    "follow",
    "unfollow",
)


def upgrade() -> None:
    signal_type_enum = postgresql.ENUM(*SIGNAL_TYPES, name="signal_type")
    signal_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "interaction_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", signal_type_enum, nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_interaction_signals_user_id", "interaction_signals", ["user_id"])
    op.create_index("ix_interaction_signals_post_id", "interaction_signals", ["post_id"])
    op.create_index("ix_interaction_signals_creator_id", "interaction_signals", ["creator_id"])
    op.create_index("ix_interaction_signals_user_type", "interaction_signals", ["user_id", "signal_type"])
    op.create_index("ix_interaction_signals_post_type", "interaction_signals", ["post_id", "signal_type"])
    op.create_index("ix_interaction_signals_creator_type", "interaction_signals", ["creator_id", "signal_type"])


def downgrade() -> None:
    op.drop_index("ix_interaction_signals_creator_type", table_name="interaction_signals")
    op.drop_index("ix_interaction_signals_post_type", table_name="interaction_signals")
    op.drop_index("ix_interaction_signals_user_type", table_name="interaction_signals")
    op.drop_index("ix_interaction_signals_creator_id", table_name="interaction_signals")
    op.drop_index("ix_interaction_signals_post_id", table_name="interaction_signals")
    op.drop_index("ix_interaction_signals_user_id", table_name="interaction_signals")
    op.drop_table("interaction_signals")

    postgresql.ENUM(*SIGNAL_TYPES, name="signal_type").drop(op.get_bind(), checkfirst=True)
