"""Enable pgvector extension and create embedding tables.

Revision ID: 002_pgvector
Revises: 001
Create Date: 2026-07-07 00:00:00.000000
"""

revision = "002_pgvector"
down_revision = "001"
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# pgvector is imported for the Vector column type
from pgvector.sqlalchemy import Vector

EMBEDDING_DIM = 384


def upgrade() -> None:
    # ── Enable pgvector extension ────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── user_embeddings ──────────────────────────────────────────
    op.create_table(
        "user_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("source_text_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_embeddings_user_id", "user_embeddings", ["user_id"])

    # IVFFlat index for ANN search on user embeddings
    # Note: IVFFlat requires the table to have data before index creation.
    # In production, populate data first, then create the index.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_embeddings_ivfflat
        ON user_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )

    # ── content_embeddings ───────────────────────────────────────
    op.create_table(
        "content_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("source_text_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("post_id"),
    )
    op.create_index("ix_content_embeddings_post_id", "content_embeddings", ["post_id"])

    # IVFFlat index for ANN search on content embeddings
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_content_embeddings_ivfflat
        ON content_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.drop_table("content_embeddings")
    op.drop_table("user_embeddings")
    # Do NOT drop the vector extension — other tables or future migrations may use it