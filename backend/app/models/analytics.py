"""
Recommendation-ready analytics — a unified, append-only log of engagement
signals across posts and creators.

The existing tables (``post_likes``, ``post_saves``, ``post_shares``,
``post_watches``, ``follows``) remain the source of truth for idempotent
toggle state and denormalized counters. ``InteractionSignal`` complements
them with a single flat event stream purpose-built for recommendation
feature extraction (e.g. "posts this user watched to completion",
"creators this user engages with most"), so a feature pipeline doesn't
need to join across five different tables.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SignalType(str, enum.Enum):
    """Recommendation-relevant engagement signal kinds."""

    VIEW = "view"
    WATCH_DURATION = "watch_duration"
    COMPLETION = "completion"
    REWATCH = "rewatch"
    LIKE = "like"
    UNLIKE = "unlike"
    SAVE = "save"
    UNSAVE = "unsave"
    SHARE = "share"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"


class InteractionSignal(Base, TimestampMixin):
    """One row per recommendation-relevant engagement event.

    ``post_id`` is null for creator-level signals (follow/unfollow).
    ``creator_id`` is the content owner for post signals, or the followed
    user for follow signals — always present so creator-affinity features
    can be computed without joining back to ``posts``.
    ``value`` carries the signal's magnitude where relevant (e.g. watched
    seconds for ``WATCH_DURATION``, 1.0 otherwise).
    """

    __tablename__ = "interaction_signals"
    __table_args__ = (
        Index("ix_interaction_signals_user_type", "user_id", "signal_type"),
        Index("ix_interaction_signals_post_type", "post_id", "signal_type"),
        Index("ix_interaction_signals_creator_type", "creator_id", "signal_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType, name="signal_type"), nullable=False)
    value: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
