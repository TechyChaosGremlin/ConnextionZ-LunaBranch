"""Complete comment moderation and notification persistence.

Revision ID: 20260820_0019
Revises: 20260820_0018
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0019"
down_revision: Union[str, None] = "20260820_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "moderation_status" not in {column["name"] for column in sa.inspect(bind).get_columns("comments")}:
        with op.batch_alter_table("comments") as batch:
            batch.add_column(sa.Column("moderation_status", sa.String(length=20), nullable=False, server_default="approved"))
            batch.create_index("ix_comments_moderation_status", ["moderation_status"])
    if "comment_reports" not in tables:
        op.create_table(
            "comment_reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("comment_id", sa.Integer(), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reason", sa.String(length=120), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("comment_id", "reporter_id", name="uq_comment_reports_pair"),
        )
        op.create_index("ix_comment_reports_id", "comment_reports", ["id"])
        op.create_index("ix_comment_reports_comment_id", "comment_reports", ["comment_id"])
        op.create_index("ix_comment_reports_reporter_id", "comment_reports", ["reporter_id"])
        op.create_index("ix_comment_reports_created_at", "comment_reports", ["created_at"])
    if "notifications" not in tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.String(length=30), nullable=False),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=True),
            sa.Column("comment_id", sa.Integer(), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        for column in ("id", "recipient_id", "actor_id", "type", "post_id", "comment_id", "created_at"):
            op.create_index(f"ix_notifications_{column}", "notifications", [column])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("comment_reports")
    with op.batch_alter_table("comments") as batch:
        batch.drop_index("ix_comments_moderation_status")
        batch.drop_column("moderation_status")