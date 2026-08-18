"""Add relationship lookup indexes.

Revision ID: 20260817_0007
Revises: 20260817_0006
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260817_0007"
down_revision: Union[str, None] = "20260817_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_follows_follower_id", "follows", ["follower_id"])
    op.create_index("ix_follows_following_id", "follows", ["following_id"])
    op.create_index("ix_posts_profile_id", "posts", ["profile_id"])
    op.create_index("ix_playlists_profile_id", "playlists", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_playlists_profile_id", table_name="playlists")
    op.drop_index("ix_posts_profile_id", table_name="posts")
    op.drop_index("ix_follows_following_id", table_name="follows")
    op.drop_index("ix_follows_follower_id", table_name="follows")