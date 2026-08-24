"""
User repository for database operations.

Provides CRUD operations for User model.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Profile, User, UserRole
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model database operations.

    Extends BaseRepository with common CRUD operations and adds
    user-specific query methods.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: Email address to search for

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_users_by_role(self, role: UserRole) -> list[User]:
        """
        Get all users with a specific role.

        Args:
            role: UserRole to filter by

        Returns:
            List of User objects
        """
        result = await self.db.execute(select(User).where(User.role == role))
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        user = await self.get_by_email(email)
        return user is not None

    async def username_exists(self, username: str) -> bool:
        """
        Check if username already exists.

        Args:
            username: Username to check

        Returns:
            True if username exists, False otherwise
        """
        user = await self.get_by_username(username)
        return user is not None

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get all active (non-deleted) users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active User objects
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            is_active=True,
        )

    async def search_by_username_and_display_name(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> list[tuple[User, float]]:
        """
        Search users by username and display_name with relevance ranking.
        
        Ranking algorithm (via SQL case expression):
        - Exact username match: 100
        - Username prefix match: 70
        - Display name prefix match: 55
        - Username contains: 35
        - Display name contains: 25
        - Default: 10

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of (User, rank_score) tuples sorted by relevance
        """
        terms = [term for term in query.strip().split() if term]
        if not terms:
            return []

        # Build patterns for matching
        contains_pattern = "%" + "%".join(terms) + "%"
        prefix_pattern = terms[0] + "%"
        exact_value = " ".join(terms)

        # Build rank score using SQL case expression
        rank_score = case(
            (func.lower(User.username) == exact_value.lower(), 100),
            (func.lower(User.username).ilike(prefix_pattern), 70),
            (func.lower(Profile.display_name).ilike(prefix_pattern), 55),
            (func.lower(User.username).ilike(contains_pattern), 35),
            (func.lower(Profile.display_name).ilike(contains_pattern), 25),
            else_=10,
        )

        # Build the query
        stmt = (
            select(User, rank_score.label("rank_score"))
            .join(Profile, User.id == Profile.user_id)
            .where(
                or_(
                    func.lower(User.username).ilike(contains_pattern),
                    func.lower(Profile.display_name).ilike(contains_pattern),
                )
            )
            .order_by(desc("rank_score"), Profile.follower_count.desc(), User.username)
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return [(user, score) for user, score in result.all()]
