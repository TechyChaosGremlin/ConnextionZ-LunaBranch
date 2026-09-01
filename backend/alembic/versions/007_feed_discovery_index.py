"""Composite index to support the For You feed's discovery-pool query
(recent published posts ordered by created_at, independent of user_id).

Revision ID: 007
Revises: 006
Create Date: 2026-09-01 00:00:00.000000
"""

from alembic import op


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_posts_status_created_at",
        "posts",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_posts_status_created_at", table_name="posts")
