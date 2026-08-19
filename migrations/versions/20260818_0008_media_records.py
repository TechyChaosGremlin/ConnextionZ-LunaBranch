"""Add server-owned media records for posts.

Revision ID: 20260818_0008
Revises: 20260817_0007
Create Date: 2026-08-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260818_0008"
down_revision: Union[str, None] = "20260817_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "media" not in inspector.get_table_names():
        op.create_table(
            "media",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_media_user_id", "media", ["user_id"])

    columns = {column["name"] for column in inspector.get_columns("posts")}
    with op.batch_alter_table("posts") as batch:
        if "media_id" not in columns:
            batch.add_column(sa.Column("media_id", sa.Integer(), nullable=True))
        if "thumbnail_media_id" not in columns:
            batch.add_column(sa.Column("thumbnail_media_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_posts_media_id", "media", ["media_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_posts_thumbnail_media_id", "media", ["thumbnail_media_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_posts_media_id", ["media_id"])
        batch.create_index("ix_posts_thumbnail_media_id", ["thumbnail_media_id"])


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch:
        batch.drop_index("ix_posts_thumbnail_media_id")
        batch.drop_index("ix_posts_media_id")
        batch.drop_constraint("fk_posts_thumbnail_media_id", type_="foreignkey")
        batch.drop_constraint("fk_posts_media_id", type_="foreignkey")
        batch.drop_column("thumbnail_media_id")
        batch.drop_column("media_id")
    op.drop_index("ix_media_user_id", table_name="media")
    op.drop_table("media")