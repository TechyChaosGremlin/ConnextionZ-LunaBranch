"""Store full post metadata.

Revision ID: 20260816_0004
Revises: 20260816_0003
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0004"
down_revision: Union[str, None] = "20260816_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("hashtags", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("audio", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("visibility", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("allow_comments", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("allow_collabs", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("duration_sec", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("comments", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("shares", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("saves", sa.Integer(), nullable=True))

    op.execute("UPDATE posts SET hashtags = '[]' WHERE hashtags IS NULL")
    op.execute("UPDATE posts SET audio = 'Original Sound' WHERE audio IS NULL")
    op.execute("UPDATE posts SET visibility = 'public' WHERE visibility IS NULL")
    op.execute("UPDATE posts SET allow_comments = 1 WHERE allow_comments IS NULL")
    op.execute("UPDATE posts SET allow_collabs = 1 WHERE allow_collabs IS NULL")
    op.execute("UPDATE posts SET duration_sec = 0 WHERE duration_sec IS NULL")
    op.execute("UPDATE posts SET comments = 0 WHERE comments IS NULL")
    op.execute("UPDATE posts SET shares = 0 WHERE shares IS NULL")
    op.execute("UPDATE posts SET saves = 0 WHERE saves IS NULL")

    with op.batch_alter_table("posts") as batch_op:
        batch_op.alter_column("hashtags", existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column("audio", existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("visibility", existing_type=sa.String(length=20), nullable=False)
        batch_op.alter_column("allow_comments", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column("allow_collabs", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column("duration_sec", existing_type=sa.Float(), nullable=False)
        batch_op.alter_column("comments", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("shares", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("saves", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        for column in (
            "saves", "shares", "comments", "duration_sec", "allow_collabs",
            "allow_comments", "visibility", "audio", "hashtags",
        ):
            batch_op.drop_column(column)