"""Add post saves.

Revision ID: 20260820_0011
Revises: 20260819_0010
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0011"
down_revision: Union[str, None] = "20260819_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "post_saves" in inspector.get_table_names():
        return

    op.create_table(
        "post_saves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_saves_pair"),
    )
    op.create_index(op.f("ix_post_saves_id"), "post_saves", ["id"], unique=False)
    op.create_index(op.f("ix_post_saves_post_id"), "post_saves", ["post_id"], unique=False)
    op.create_index(op.f("ix_post_saves_user_id"), "post_saves", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "post_saves" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_post_saves_user_id"), table_name="post_saves")
    op.drop_index(op.f("ix_post_saves_post_id"), table_name="post_saves")
    op.drop_index(op.f("ix_post_saves_id"), table_name="post_saves")
    op.drop_table("post_saves")
