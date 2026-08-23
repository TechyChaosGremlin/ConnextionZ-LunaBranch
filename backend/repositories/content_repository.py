"""
Content repository for database operations.

Provides CRUD operations for Post, Comment, and Media models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Post, Comment, Media, ContentType, ContentStatus
from repositories.base import BaseRepository


class PostRepository(BaseRepository[Post]):
    """Repository for Post model database operations.

    Extends BaseRepository with common CRUD operations and adds
    post-specific query methods for feeds, pagination, and interactions.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Post)

    async def get_by_id(self, post_id: uuid.UUID, include_deleted: bool = False) -> Optional[Post]:
        """
        Get post by ID.

        Args:
            post_id: Post ID (UUID)
            include_deleted: Whether to include soft-deleted posts

        Returns:
            Post object or None if not found
        """
        stmt = select(Post).where(Post.id == post_id)
        if not include_deleted:
            stmt = stmt.where(Post.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: Optional[ContentStatus] = None,
        limit: int = 20,
        before_id: Optional[uuid.UUID] = None,
    ) -> list[Post]:
        """
        Get posts by user, ordered by created_at DESC.

        Args:
            user_id: User ID to filter by
            status: Optional content status filter
            limit: Maximum number of posts to return
            before_id: Cursor for pagination (UUIDv7)

        Returns:
            List of Post objects
        """
        stmt = select(Post).where(
            Post.user_id == user_id,
            Post.deleted_at.is_(None),
        )
        if status:
            stmt = stmt.where(Post.status == status)
        if before_id:
            # Cursor-based pagination using UUIDv7 time-sort
            stmt = stmt.where(Post.id < before_id)
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_feed(
        self,
        user_ids: list[uuid.UUID],
        content_types: Optional[list[ContentType]] = None,
        limit: int = 20,
        before_id: Optional[uuid.UUID] = None,
    ) -> list[Post]:
        """
        Get a feed of published posts from specified users.

        Args:
            user_ids: List of user IDs to include in feed
            content_types: Optional filter by content types
            limit: Maximum number of posts to return
            before_id: Cursor for pagination (UUIDv7)

        Returns:
            List of Post objects
        """
        stmt = select(Post).where(
            Post.user_id.in_(user_ids),
            Post.status == ContentStatus.PUBLISHED,
            Post.deleted_at.is_(None),
        )
        if content_types:
            stmt = stmt.where(Post.content_type.in_(content_types))
        if before_id:
            stmt = stmt.where(Post.id < before_id)
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, post_id: uuid.UUID) -> bool:
        """
        Soft-delete a post.

        Args:
            post_id: Post ID to soft delete

        Returns:
            True if post was found and soft-deleted, False otherwise
        """
        post = await self.get_by_id(post_id)
        if not post:
            return False
        post.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def like_post(self, post_id: uuid.UUID) -> int:
        """
        Increment like count on a post.

        Args:
            post_id: Post ID to like

        Returns:
            New like count

        Raises:
            ValueError: If post not found
        """
        post = await self.get_by_id(post_id)
        if not post:
            raise ValueError("Post not found")
        post.like_count += 1
        await self.db.flush()
        return post.like_count

    async def get_total_count(self) -> int:
        """
        Get total count of non-deleted posts.

        Returns:
            Count of active posts
        """
        result = await self.db.execute(
            select(func.count()).select_from(Post).where(Post.deleted_at.is_(None))
        )
        return result.scalar_one()


class CommentRepository(BaseRepository[Comment]):
    """Repository for Comment model database operations.

    Extends BaseRepository with common CRUD operations and adds
    comment-specific methods for threading and post associations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Comment)

    async def get_by_id(self, comment_id: uuid.UUID) -> Optional[Comment]:
        """
        Get comment by ID.

        Args:
            comment_id: Comment ID (UUID)

        Returns:
            Comment object or None if not found
        """
        result = await self.db.execute(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_post_id(
        self,
        post_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> list[Comment]:
        """
        Get comments for a post, optionally filtered by parent for threading.

        Args:
            post_id: Post ID to get comments for
            parent_id: Optional parent ID for threaded comments
            limit: Maximum number of comments to return

        Returns:
            List of Comment objects
        """
        stmt = select(Comment).where(
            Comment.post_id == post_id,
            Comment.deleted_at.is_(None),
        )
        if parent_id is not None:
            stmt = stmt.where(Comment.parent_id == parent_id)
        else:
            # Top-level comments only (parent_id IS NULL)
            stmt = stmt.where(Comment.parent_id.is_(None))
        stmt = stmt.order_by(Comment.created_at.asc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, comment_id: uuid.UUID) -> bool:
        """
        Soft-delete a comment.

        Args:
            comment_id: Comment ID to soft delete

        Returns:
            True if comment was found and soft-deleted, False otherwise
        """
        comment = await self.get_by_id(comment_id)
        if not comment:
            return False
        comment.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
