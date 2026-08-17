"""Create the initial profile API schema.

Revision ID: 20260816_0001
Revises:
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("avatar_color", sa.String(length=50), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("online", sa.Boolean(), nullable=False),
        sa.Column("collab_status", sa.String(length=120), nullable=True),
        sa.Column("collab_score", sa.Float(), nullable=False),
        sa.Column("collab_count", sa.Integer(), nullable=False),
        sa.Column("followers", sa.Integer(), nullable=False),
        sa.Column("following", sa.Integer(), nullable=False),
        sa.Column("open_to_collab", sa.Boolean(), nullable=False),
        sa.Column("response_time", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_profiles_id", "profiles", ["id"], unique=False)
    op.create_index("ix_profiles_username", "profiles", ["username"], unique=True)

    op.create_table(
        "follows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("follower_id", sa.Integer(), nullable=False),
        sa.Column("following_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["following_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follower_id", "following_id", name="uq_follows_pair"),
    )
    op.create_index("ix_follows_id", "follows", ["id"], unique=False)

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("thumbnail", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("collab_with", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posts_id", "posts", ["id"], unique=False)

    op.create_table(
        "playlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("cover", sa.String(length=500), nullable=False),
        sa.Column("item_label", sa.String(length=80), nullable=False),
        sa.Column("plays", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_playlists_id", "playlists", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_playlists_id", table_name="playlists")
    op.drop_table("playlists")
    op.drop_index("ix_posts_id", table_name="posts")
    op.drop_table("posts")
    op.drop_index("ix_follows_id", table_name="follows")
    op.drop_table("follows")
    op.drop_index("ix_profiles_username", table_name="profiles")
    op.drop_index("ix_profiles_id", table_name="profiles")
    op.drop_table("profiles")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
