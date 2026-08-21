"""Search history/trending table and supporting indexes.

Revision ID: 20260821_0020
Revises: 20260820_0019
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0020"
down_revision: Union[str, None] = "20260820_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "search_queries" not in tables:
        op.create_table(
            "search_queries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("query_text", sa.String(length=200), nullable=False),
            sa.Column("normalized_query", sa.String(length=200), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_search_queries_id", "search_queries", ["id"])
        op.create_index("ix_search_queries_user_id", "search_queries", ["user_id"])
        op.create_index("ix_search_queries_normalized_query", "search_queries", ["normalized_query"])
        op.create_index("ix_search_queries_created_at", "search_queries", ["created_at"])

    profile_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("profiles")}
    if "ix_profiles_display_name" not in profile_indexes:
        op.create_index("ix_profiles_display_name", "profiles", ["display_name"])

    post_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("posts")}
    if "ix_posts_audio" not in post_indexes:
        op.create_index("ix_posts_audio", "posts", ["audio"])
    if "ix_posts_status_moderation_status" not in post_indexes:
        op.create_index("ix_posts_status_moderation_status", "posts", ["status", "moderation_status"])


def downgrade() -> None:
    op.drop_index("ix_posts_status_moderation_status", table_name="posts")
    op.drop_index("ix_posts_audio", table_name="posts")
    op.drop_index("ix_profiles_display_name", table_name="profiles")
    op.drop_table("search_queries")
