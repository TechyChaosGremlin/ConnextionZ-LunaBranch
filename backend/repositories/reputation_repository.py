"""
Reputation repository for database operations.

Provides CRUD operations for ReputationScore, Endorsement, and Badge models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reputation import (
    ReputationScore, Endorsement, Badge,
    EndorsementStatus,
)
from repositories.base import BaseRepository


class ReputationRepository:
    """Repository for ReputationScore and Endorsement models.

    Uses composition pattern: holds ReputationScoreRepository for score
    management and handles endorsements and badges directly.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_endorsement(self, endorsement: Endorsement) -> Endorsement:
        """Create a new endorsement."""
        self.db.add(endorsement)
        await self.db.flush()
        await self.db.refresh(endorsement)
        return endorsement

    async def get_endorsement_by_id(self, endorsement_id: uuid.UUID) -> Optional[Endorsement]:
        """Get endorsement by ID."""
        result = await self.db.execute(
            select(Endorsement).where(Endorsement.id == endorsement_id)
        )
        return result.scalar_one_or_none()

    async def get_endorsements_for_user(
        self,
        user_id: uuid.UUID,
        status: Optional[EndorsementStatus] = None,
        limit: int = 20,
    ) -> List[Endorsement]:
        """Get endorsements received by a user."""
        stmt = select(Endorsement).where(
            Endorsement.endorsed_user_id == user_id
        )
        if status:
            stmt = stmt.where(Endorsement.status == status)
        stmt = stmt.order_by(Endorsement.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_reputation_score(self, user_id: uuid.UUID) -> Optional[ReputationScore]:
        """Get reputation score for a user."""
        result = await self.db.execute(
            select(ReputationScore).where(ReputationScore.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_reputation_score(
        self, user_id: uuid.UUID
    ) -> ReputationScore:
        """Recalculate and update reputation score for a user."""
        # Get or create reputation score
        score = await self.get_reputation_score(user_id)
        if not score:
            score = ReputationScore(user_id=user_id)
            self.db.add(score)

        # Calculate score based on endorsements, content, etc.
        # This is a simplified calculation
        endorsement_count = await self._count_endorsements(user_id)
        score.endorsement_count = endorsement_count
        score.overall_score = min(100, endorsement_count * 10)  # Simple formula
        score.last_calculated_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(score)
        return score

    async def _count_endorsements(self, user_id: uuid.UUID) -> int:
        """Count endorsements for a user."""
        stmt = select(func.count(Endorsement.id)).where(
            Endorsement.endorsed_user_id == user_id,
            Endorsement.status == EndorsementStatus.APPROVED,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_available_badges(self) -> List[Badge]:
        """Get all available badge definitions."""
        result = await self.db.execute(
            select(Badge).where(Badge.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_user_badges(self, user_id: uuid.UUID) -> List[Badge]:
        """Get badges earned by a user."""
        # This would require a user_badges association table
        # For now, return empty list
        return []
