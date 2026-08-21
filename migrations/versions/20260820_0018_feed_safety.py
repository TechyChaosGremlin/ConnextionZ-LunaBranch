"""Add persistence for feed safety controls.

Revision ID: 20260820_0018
Revises: 20260820_0017
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260820_0018"
down_revision: Union[str, None] = "20260820_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "user_blocks" not in tables:
        op.create_table(
            "user_blocks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("blocker_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("blocked_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_pair"),
        )
        op.create_index("ix_user_blocks_id", "user_blocks", ["id"])
        op.create_index("ix_user_blocks_blocker_id", "user_blocks", ["blocker_id"])
        op.create_index("ix_user_blocks_blocked_id", "user_blocks", ["blocked_id"])
    if "user_mutes" not in tables:
        op.create_table(
            "user_mutes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("muter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("muted_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("muter_id", "muted_id", name="uq_user_mutes_pair"),
        )
        op.create_index("ix_user_mutes_id", "user_mutes", ["id"])
        op.create_index("ix_user_mutes_muter_id", "user_mutes", ["muter_id"])
        op.create_index("ix_user_mutes_muted_id", "user_mutes", ["muted_id"])
    if "post_reports" not in tables:
        op.create_table(
            "post_reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("post_id", "reporter_id", name="uq_post_reports_pair"),
        )
        op.create_index("ix_post_reports_id", "post_reports", ["id"])
        op.create_index("ix_post_reports_post_id", "post_reports", ["post_id"])
        op.create_index("ix_post_reports_reporter_id", "post_reports", ["reporter_id"])
    if "moderation_status" not in {column["name"] for column in sa.inspect(bind).get_columns("posts")}:
        with op.batch_alter_table("posts") as batch:
            batch.add_column(sa.Column("moderation_status", sa.String(length=20), nullable=False, server_default="approved"))
            batch.create_index("ix_posts_moderation_status", ["moderation_status"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "post_reports" in tables:
        op.drop_table("post_reports")
    if "user_mutes" in tables:
        op.drop_table("user_mutes")
    if "user_blocks" in tables:
        op.drop_table("user_blocks")
    if "moderation_status" in {column["name"] for column in sa.inspect(bind).get_columns("posts")}:
        with op.batch_alter_table("posts") as batch:
            batch.drop_index("ix_posts_moderation_status")
            batch.drop_column("moderation_status")