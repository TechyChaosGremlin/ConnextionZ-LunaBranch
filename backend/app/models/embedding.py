"""
Embedding models — vector representations for Two-Tower recommendation.

Uses pgvector for efficient ANN (Approximate Nearest Neighbor) search.
Embedding dimension: 384 (all-MiniLM-L6-v2 default).
"""

from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

# Default embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIM = 384


# ── UserEmbedding ────────────────────────────────────────────────


class UserEmbedding(Base, TimestampMixin):
    """Vector embedding for a user (Creator Tower).

    Generated from profile text, bio, tags, and content history.
    Used for creator discovery and personalized feed ranking.
    """

    __tablename__ = "user_embeddings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=False
    )

    # Metadata
    model_name: Mapped[str] = mapped_column(
        String(128), default="all-MiniLM-L6-v2", nullable=False
    )
    model_version: Mapped[str] = mapped_column(
        String(32), default="1.0", nullable=False
    )
    source_text_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # SHA-256 of source text for cache invalidation

    def __repr__(self) -> str:
        return f"<UserEmbedding user={self.user_id!r} model={self.model_name!r}>"


# ── ContentEmbedding ─────────────────────────────────────────────


class ContentEmbedding(Base, TimestampMixin):
    """Vector embedding for a content item (Item Tower).

    Generated from post title, body, caption, and tags.
    Used for content-based recommendations and similar-content discovery.
    """

    __tablename__ = "content_embeddings"

    post_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=False
    )

    # Metadata
    model_name: Mapped[str] = mapped_column(
        String(128), default="all-MiniLM-L6-v2", nullable=False
    )
    model_version: Mapped[str] = mapped_column(
        String(32), default="1.0", nullable=False
    )
    source_text_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ContentEmbedding post={self.post_id!r} model={self.model_name!r}>"