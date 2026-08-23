"""
Reputation models — scores, endorsements, and badges.

Covers the Reputation System feature for creator trust and discovery.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


# ── ReputationScore ──────────────────────────────────────────────


class ReputationScore(Base, TimestampMixin):
    """Aggregate reputation score for a user, recomputed periodically."""

    __tablename__ = "reputation_scores"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Composite score (0.0 – 100.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Sub-scores
    collaboration_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    content_quality_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    community_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Raw counts
    total_endorsements: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    completed_collaborations: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    on_time_delivery_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    # Score metadata
    score_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    computed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<ReputationScore user={self.user_id!r} score={self.overall_score:.1f}>"


# ── Endorsement ──────────────────────────────────────────────────


class Endorsement(Base, TimestampMixin):
    """An endorsement from one user to another — builds reputation."""

    __tablename__ = "endorsements"

    endorser_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endorsee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Endorsement details
    category: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "collaboration", "creativity", "reliability", "communication"
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 1–5 star rating

    # Context
    collaboration_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("collaborations.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Endorsement from={self.endorser_id!r} to={self.endorsee_id!r} rating={self.rating}>"


# ── Badge ────────────────────────────────────────────────────────


class Badge(Base, TimestampMixin):
    """A badge definition — e.g., "Top Collaborator", "Rising Star"."""

    __tablename__ = "badges"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "collaboration", "content", "community", "milestone"
    tier: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # 1=bronze, 2=silver, 3=gold, 4=platinum
    criteria: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # e.g., {"min_collaborations": 10}

    def __repr__(self) -> str:
        return f"<Badge name={self.name!r} tier={self.tier}>"


# ── UserBadge ────────────────────────────────────────────────────


class UserBadge(Base, TimestampMixin):
    """Join table — badges awarded to users."""

    __tablename__ = "user_badges"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    awarded_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    awarded_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )  # system or admin user

    def __repr__(self) -> str:
        return f"<UserBadge user={self.user_id!r} badge={self.badge_id!r}>"