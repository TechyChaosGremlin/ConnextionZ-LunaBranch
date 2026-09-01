"""
Notification model — real-time and persisted notifications.

Covers the Notifications feature (in-app, push, email).
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    COLLABORATION_INVITE = "collaboration_invite"
    COLLABORATION_ACCEPTED = "collaboration_accepted"
    COLLABORATION_COMPLETED = "collaboration_completed"
    NEW_FOLLOWER = "new_follower"
    NEW_COMMENT = "new_comment"
    NEW_LIKE = "new_like"
    MENTION = "mention"
    MESSAGE = "message"
    BADGE_EARNED = "badge_earned"
    ENDORSEMENT_RECEIVED = "endorsement_received"
    MILESTONE_COMPLETED = "milestone_completed"
    SYSTEM = "system"


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"


class Notification(Base, TimestampMixin):
    """A notification delivered to a user."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "type", "actor_id", "event_key",
            name="uq_notification_event_delivery",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification content
    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            name="notification_type",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # payload for deep-linking
    event_key: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Delivery
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            name="notification_channel",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
        default=NotificationChannel.IN_APP,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Sender context (nullable for system notifications)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Notification user={self.user_id!r} type={self.type.value!r} read={self.is_read!r}>"