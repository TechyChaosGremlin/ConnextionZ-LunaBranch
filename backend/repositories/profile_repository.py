"""
Profile repository for database operations.

Provides CRUD operations for Profile model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Profile, User
from repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    """
    Repository for Profile model database operations.

    Extends BaseRepository with common CRUD operations and adds
    profile-specific lookup methods (by username, by user IDs).
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Profile)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Profile]:
        """
        Get profile by user ID.

        Args:
            user_id: User ID (UUID)

        Returns:
            Profile object or None if not found
        """
        result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[Profile]:
        """
        Get profile by username (via User relationship).

        Args:
            username: Username string

        Returns:
            Profile object or None if not found
        """
        result = await self.db.execute(
            select(Profile)
            .join(User, Profile.user_id == User.id)
            .where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_multiple_by_user_ids(
        self, user_ids: list[uuid.UUID]
    ) -> list[Profile]:
        """
        Get multiple profiles by user IDs.

        Args:
            user_ids: List of user IDs (UUIDs)

        Returns:
            List of Profile objects
        """
        result = await self.db.execute(
            select(Profile).where(Profile.user_id.in_(user_ids))
        )
        return list(result.scalars().all())
