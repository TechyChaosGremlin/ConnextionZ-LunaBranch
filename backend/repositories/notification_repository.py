"""
Notification repository for database operations.

Provides CRUD operations for Notification model.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification, NotificationType, NotificationStatus,
)
from repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification model database operations.

    Extends BaseRepository with common CRUD operations and adds
    notification-specific methods for user queries and read status management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Notification)

    async def get_for_user(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 20,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[Notification]:
        """Get notifications for a user."""
        stmt = select(Notification).where(
            Notification.recipient_id == user_id
        )
        if unread_only:
            stmt = stmt.where(Notification.status != NotificationStatus.READ)
        if before_id:
            stmt = stmt.where(Notification.id < before_id)
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread notifications for a user."""
        stmt = select(func.count(Notification.id)).where(
            Notification.recipient_id == user_id,
            Notification.status != NotificationStatus.READ,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification: Notification) -> Notification:
        """Mark a notification as read."""
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all notifications as read for a user. Returns count of updated notifications."""
        stmt = (
            update(Notification)
            .where(
                Notification.recipient_id == user_id,
                Notification.status != NotificationStatus.READ,
            )
            .values(
                status=NotificationStatus.READ,
                read_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount
