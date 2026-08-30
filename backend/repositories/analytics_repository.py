"""Unified recommendation-ready engagement signal log.

See ``app.models.analytics.InteractionSignal`` for the rationale — this
repository is the single write/read path for that append-only event
stream, kept separate from the toggle-state repositories in
``social_repository`` so feature-extraction queries don't have to touch
five different tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import InteractionSignal, SignalType
from repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[InteractionSignal]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, InteractionSignal)

    async def record(
        self,
        *,
        user_id: uuid.UUID,
        creator_id: uuid.UUID,
        signal_type: SignalType,
        post_id: uuid.UUID | None = None,
        value: float = 1.0,
    ) -> InteractionSignal:
        signal = InteractionSignal(
            user_id=user_id,
            post_id=post_id,
            creator_id=creator_id,
            signal_type=signal_type,
            value=value,
        )
        self.db.add(signal)
        await self.db.flush()
        return signal

    async def get_for_post(self, post_id: uuid.UUID, limit: int = 500) -> list[InteractionSignal]:
        result = await self.db.execute(
            select(InteractionSignal)
            .where(InteractionSignal.post_id == post_id)
            .order_by(InteractionSignal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_user(self, user_id: uuid.UUID, limit: int = 500) -> list[InteractionSignal]:
        result = await self.db.execute(
            select(InteractionSignal)
            .where(InteractionSignal.user_id == user_id)
            .order_by(InteractionSignal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def signal_totals(
        self,
        *,
        creator_id: uuid.UUID | None = None,
        post_id: uuid.UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[SignalType, dict[str, float]]:
        """Per-signal-type event count + summed value, scoped to a creator and/or
        post and/or date range — powers the creator/post analytics dashboard."""
        stmt = select(
            InteractionSignal.signal_type,
            func.count().label("cnt"),
            func.sum(InteractionSignal.value).label("total"),
        ).group_by(InteractionSignal.signal_type)
        if creator_id is not None:
            stmt = stmt.where(InteractionSignal.creator_id == creator_id)
        if post_id is not None:
            stmt = stmt.where(InteractionSignal.post_id == post_id)
        if start is not None:
            stmt = stmt.where(InteractionSignal.created_at >= start)
        if end is not None:
            stmt = stmt.where(InteractionSignal.created_at <= end)
        result = await self.db.execute(stmt)
        return {
            row.signal_type: {"count": row.cnt, "total": float(row.total or 0.0)}
            for row in result.all()
        }

    async def creator_affinity(self, user_id: uuid.UUID, limit: int = 20) -> list[tuple[uuid.UUID, float]]:
        """Creators this user engages with most, weighted by signal value."""
        result = await self.db.execute(
            select(InteractionSignal.creator_id, func.sum(InteractionSignal.value).label("score"))
            .where(InteractionSignal.user_id == user_id)
            .group_by(InteractionSignal.creator_id)
            .order_by(func.sum(InteractionSignal.value).desc())
            .limit(limit)
        )
        return [(row[0], float(row[1])) for row in result.all()]
