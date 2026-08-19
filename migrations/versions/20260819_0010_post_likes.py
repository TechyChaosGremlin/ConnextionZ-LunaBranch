"""Add post likes.

Revision ID: 20260819_0010
Revises: 20260819_0009
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260819_0010"
down_revision: Union[str, None] = "20260819_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "post_likes" in inspector.get_table_names():
        return

    op.create_table(
        "post_likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_likes_pair"),
    )
    op.create_index(op.f("ix_post_likes_id"), "post_likes", ["id"], unique=False)
    op.create_index(op.f("ix_post_likes_post_id"), "post_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_post_likes_user_id"), "post_likes", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "post_likes" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_post_likes_user_id"), table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_post_id"), table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_id"), table_name="post_likes")
    op.drop_table("post_likes")