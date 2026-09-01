"""
Notification repository for database operations.

Provides CRUD operations for Notification model.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import exists, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification, NotificationType, NotificationChannel,
)
from app.models.social import UserBlock, UserMute
from repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification model database operations.

    Extends BaseRepository with common CRUD operations and adds
    notification-specific methods for user queries and read status management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Notification)

    @staticmethod
    def _visible_to_user(user_id: uuid.UUID):
        """Return the shared filter for actors the recipient permits to notify them."""
        muted_actor = exists().where(
            UserMute.muter_id == user_id,
            UserMute.muted_id == Notification.actor_id,
        )
        recipient_blocked_actor = exists().where(
            UserBlock.blocker_id == user_id,
            UserBlock.blocked_id == Notification.actor_id,
        )
        actor_blocked_recipient = exists().where(
            UserBlock.blocker_id == Notification.actor_id,
            UserBlock.blocked_id == user_id,
        )
        return ~muted_actor, ~recipient_blocked_actor, ~actor_blocked_recipient

    async def get_for_user(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 20,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[Notification]:
        """Get notifications for a user."""
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            *self._visible_to_user(user_id),
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        if before_id:
            stmt = stmt.where(Notification.id < before_id)
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread notifications for a user."""
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
            *self._visible_to_user(user_id),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification: Notification) -> Notification:
        """Mark a notification as read."""
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc).isoformat()
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all notifications as read for a user. Returns count of updated notifications."""
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        body: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        data: Optional[dict] = None,
        event_key: Optional[str] = None,
    ) -> Optional[Notification]:
        """Create one eligible notification, suppressing duplicate event deliveries."""
        if user_id == actor_id:
            return None

        if actor_id is not None:
            actor_blocked_recipient = exists().where(
                UserBlock.blocker_id == actor_id,
                UserBlock.blocked_id == user_id,
            )
            recipient_blocked_actor = exists().where(
                UserBlock.blocker_id == user_id,
                UserBlock.blocked_id == actor_id,
            )
            recipient_muted_actor = exists().where(
                UserMute.muter_id == user_id,
                UserMute.muted_id == actor_id,
            )
            suppressed = await self.db.scalar(
                select(actor_blocked_recipient | recipient_blocked_actor | recipient_muted_actor)
            )
            if suppressed:
                return None

        if event_key is not None:
            existing = await self.db.scalar(
                select(Notification.id).where(
                    Notification.user_id == user_id,
                    Notification.type == type,
                    Notification.actor_id == actor_id,
                    Notification.event_key == event_key,
                )
            )
            if existing is not None:
                return None

        payload = dict(data or {})
        if event_key is not None:
            payload["event_key"] = event_key
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            actor_id=actor_id,
            channel=channel,
            data=payload or None,
            event_key=event_key,
        )
        if event_key is not None:
            result = await self.db.execute(
                insert(Notification)
                .values(
                    user_id=notification.user_id,
                    type=notification.type,
                    title=notification.title,
                    body=notification.body,
                    data=notification.data,
                    event_key=notification.event_key,
                    channel=notification.channel,
                    is_read=False,
                    actor_id=notification.actor_id,
                )
                .on_conflict_do_nothing(constraint="uq_notification_event_delivery")
                .returning(Notification)
            )
            return result.scalar_one_or_none()
        await self.create(notification)
        return notification
