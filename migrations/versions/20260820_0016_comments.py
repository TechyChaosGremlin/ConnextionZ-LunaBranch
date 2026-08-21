"""Add comments and comment likes.

Revision ID: 20260820_0016
Revises: 20260820_0015
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0016"
down_revision: Union[str, None] = "20260820_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "comments" not in tables:
        op.create_table(
            "comments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_comments_id", "comments", ["id"])
        op.create_index("ix_comments_post_id", "comments", ["post_id"])
        op.create_index("ix_comments_user_id", "comments", ["user_id"])
        op.create_index("ix_comments_created_at", "comments", ["created_at"])

    if "comment_likes" not in tables:
        op.create_table(
            "comment_likes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("comment_id", sa.Integer(), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("comment_id", "user_id", name="uq_comment_likes_pair"),
        )
        op.create_index("ix_comment_likes_id", "comment_likes", ["id"])
        op.create_index("ix_comment_likes_comment_id", "comment_likes", ["comment_id"])
        op.create_index("ix_comment_likes_user_id", "comment_likes", ["user_id"])


def downgrade() -> None:
    op.drop_table("comment_likes")
    op.drop_table("comments")