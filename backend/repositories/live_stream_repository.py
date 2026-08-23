"""
Live streaming repository for database operations.

Provides CRUD operations for LiveStream model.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import LiveStream, LiveStreamStatus
from repositories.base import BaseRepository


class LiveStreamRepository(BaseRepository[LiveStream]):
    """Repository for LiveStream model database operations.

    Extends BaseRepository with common CRUD operations and adds
    stream-specific methods for active streams, user streams, and stream lifecycle.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, LiveStream)

    async def get_active_streams(
        self,
        limit: int = 20,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[LiveStream]:
        """Get currently active live streams."""
        stmt = select(LiveStream).where(
            LiveStream.status == LiveStreamStatus.LIVE
        )
        if before_id:
            stmt = stmt.where(LiveStream.id < before_id)
        stmt = stmt.order_by(LiveStream.started_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> List[LiveStream]:
        """Get live streams for a specific user."""
        stmt = select(LiveStream).where(
            LiveStream.user_id == user_id
        ).order_by(LiveStream.started_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def end_stream(self, stream_id: uuid.UUID) -> Optional[LiveStream]:
        """End a live stream."""
        live_stream = await self.get_by_id(stream_id)
        if not live_stream:
            return None

        live_stream.status = LiveStreamStatus.ENDED
        live_stream.ended_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(live_stream)
        return live_stream
