"""Post likes/saves/shares/watches and comment likes.

Revision ID: 003
Revises: 002
Create Date: 2026-08-30 00:00:00.000000
"""

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # ── post_likes ───────────────────────────────────────────────
    op.create_table(
        "post_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_like"),
    )
    op.create_index("ix_post_likes_post_id", "post_likes", ["post_id"])
    op.create_index("ix_post_likes_user_id", "post_likes", ["user_id"])

    # ── post_saves ───────────────────────────────────────────────
    op.create_table(
        "post_saves",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_save"),
    )
    op.create_index("ix_post_saves_post_id", "post_saves", ["post_id"])
    op.create_index("ix_post_saves_user_id", "post_saves", ["user_id"])

    # ── post_shares ──────────────────────────────────────────────
    op.create_table(
        "post_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_share"),
    )
    op.create_index("ix_post_shares_post_id", "post_shares", ["post_id"])
    op.create_index("ix_post_shares_user_id", "post_shares", ["user_id"])

    # ── post_watches ─────────────────────────────────────────────
    op.create_table(
        "post_watches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watched_seconds", sa.Float(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("rewatched", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_post_watches_post_id", "post_watches", ["post_id"])
    op.create_index("ix_post_watches_user_id", "post_watches", ["user_id"])

    # ── comment_likes ────────────────────────────────────────────
    op.create_table(
        "comment_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("comment_id", "user_id", name="uq_comment_like"),
    )
    op.create_index("ix_comment_likes_comment_id", "comment_likes", ["comment_id"])
    op.create_index("ix_comment_likes_user_id", "comment_likes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_comment_likes_user_id", table_name="comment_likes")
    op.drop_index("ix_comment_likes_comment_id", table_name="comment_likes")
    op.drop_table("comment_likes")

    op.drop_index("ix_post_watches_user_id", table_name="post_watches")
    op.drop_index("ix_post_watches_post_id", table_name="post_watches")
    op.drop_table("post_watches")

    op.drop_index("ix_post_shares_user_id", table_name="post_shares")
    op.drop_index("ix_post_shares_post_id", table_name="post_shares")
    op.drop_table("post_shares")

    op.drop_index("ix_post_saves_user_id", table_name="post_saves")
    op.drop_index("ix_post_saves_post_id", table_name="post_saves")
    op.drop_table("post_saves")

    op.drop_index("ix_post_likes_user_id", table_name="post_likes")
    op.drop_index("ix_post_likes_post_id", table_name="post_likes")
    op.drop_table("post_likes")
