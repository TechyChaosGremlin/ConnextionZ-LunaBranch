"""
Repository testing patterns and fixtures.

Provides factory patterns, transactional test isolation, and common fixtures
for testing repository implementations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, AsyncTransaction
from sqlalchemy.sql import text

from app.models.user import User, UserRole
from app.models.content import Post, Comment, ContentType, ContentStatus
from app.models.profile import Profile
from repositories.user_repository import UserRepository
from repositories.content_repository import PostRepository, CommentRepository


# =============================================================================
# Factory Patterns for Test Data
# =============================================================================

class UserFactory:
    """Factory for creating User test instances."""

    @staticmethod
    def create(
        id: uuid.UUID | None = None,
        email: str | None = None,
        username: str | None = None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        **kwargs
    ) -> User:
        """
        Create a User instance for testing.

        Args:
            id: Optional UUID (generated if not provided)
            email: Optional email (generated if not provided)
            username: Optional username (generated if not provided)
            role: User role (default: USER)
            is_active: Active status (default: True)
            **kwargs: Additional User fields

        Returns:
            User instance (not persisted)
        """
        if id is None:
            id = uuid.uuid4()
        if email is None:
            email = f"test_{id.hex[:8]}@example.com"
        if username is None:
            username = f"testuser_{id.hex[:8]}"

        user = User(
            id=id,
            email=email,
            username=username,
            role=role,
            is_active=is_active,
            **kwargs
        )
        return user


class PostFactory:
    """Factory for creating Post test instances."""

    @staticmethod
    def create(
        id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        content_type: ContentType = ContentType.TEXT,
        status: ContentStatus = ContentStatus.PUBLISHED,
        title: str = "Test Post",
        **kwargs
    ) -> Post:
        """
        Create a Post instance for testing.

        Args:
            id: Optional UUID (generated if not provided)
            user_id: Optional user ID (generated if not provided)
            content_type: Content type (default: TEXT)
            status: Content status (default: PUBLISHED)
            title: Post title (default: "Test Post")
            **kwargs: Additional Post fields

        Returns:
            Post instance (not persisted)
        """
        if id is None:
            id = uuid.uuid4()
        if user_id is None:
            user_id = uuid.uuid4()

        post = Post(
            id=id,
            user_id=user_id,
            content_type=content_type,
            status=status,
            title=title,
            **kwargs
        )
        return post


class CommentFactory:
    """Factory for creating Comment test instances."""

    @staticmethod
    def create(
        id: uuid.UUID | None = None,
        post_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        content: str = "Test comment content",
        **kwargs
    ) -> Comment:
        """
        Create a Comment instance for testing.

        Args:
            id: Optional UUID (generated if not provided)
            post_id: Optional post ID (generated if not provided)
            user_id: Optional user ID (generated if not provided)
            content: Comment content (default: "Test comment content")
            **kwargs: Additional Comment fields

        Returns:
            Comment instance (not persisted)
        """
        if id is None:
            id = uuid.uuid4()
        if post_id is None:
            post_id = uuid.uuid4()
        if user_id is None:
            user_id = uuid.uuid4()

        comment = Comment(
            id=id,
            post_id=post_id,
            user_id=user_id,
            content=content,
            **kwargs
        )
        return comment


# =============================================================================
# Transactional Test Isolation
# =============================================================================

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.

    Note: In actual implementation, this should use a test database
    with transaction rollback for isolation.

    Yields:
        AsyncSession instance
    """
    # This is a placeholder - actual implementation would:
    # 1. Create a test database session
    # 2. Start a transaction
    # 3. Yield the session
    # 4. Rollback the transaction after test
    session = AsyncMock(spec=AsyncSession)
    yield session
    # Rollback would happen here


@pytest.fixture
def user_repository(db_session: AsyncSession) -> UserRepository:
    """
    Create a UserRepository instance for testing.

    Args:
        db_session: Database session fixture

    Returns:
        UserRepository instance
    """
    return UserRepository(db_session)


@pytest.fixture
def post_repository(db_session: AsyncSession) -> PostRepository:
    """
    Create a PostRepository instance for testing.

    Args:
        db_session: Database session fixture

    Returns:
        PostRepository instance
    """
    return PostRepository(db_session)


@pytest.fixture
def comment_repository(db_session: AsyncSession) -> CommentRepository:
    """
    Create a CommentRepository instance for testing.

    Args:
        db_session: Database session fixture

    Returns:
        CommentRepository instance
    """
    return CommentRepository(db_session)


# =============================================================================
# Mock Repository Pattern
# =============================================================================

class MockUserRepository:
    """
    Mock UserRepository for unit testing without database.

    Useful for testing service layer code that depends on repositories.
    """

    def __init__(self):
        self.users: dict[str, User] = {}
        self._next_id = 1

    async def create(self, user: User) -> User:
        """Mock create - stores user in memory."""
        self.users[str(user.id)] = user
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        """Mock get_by_id - retrieves from memory."""
        return self.users.get(str(user_id))

    async def get_by_email(self, email: str) -> User | None:
        """Mock get_by_email - searches in memory."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_username(self, username: str) -> User | None:
        """Mock get_by_username - searches in memory."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def update(self, user: User) -> User:
        """Mock update - updates in memory."""
        self.users[str(user.id)] = user
        return user

    async def delete(self, user: User) -> None:
        """Mock delete - removes from memory."""
        self.users.pop(str(user.id), None)

    async def email_exists(self, email: str) -> bool:
        """Mock email_exists - checks in memory."""
        return any(u.email == email for u in self.users.values())

    async def username_exists(self, username: str) -> bool:
        """Mock username_exists - checks in memory."""
        return any(u.username == username for u in self.users.values())


# =============================================================================
# Test Utilities
# =============================================================================

def assert_user_equal(user1: User, user2: User, ignore_fields: list[str] | None = None):
    """
    Assert two User instances are equal, ignoring specified fields.

    Args:
        user1: First User instance
        user2: Second User instance
        ignore_fields: List of field names to ignore in comparison
    """
    if ignore_fields is None:
        ignore_fields = []

    for field in User.__dataclass_fields__ if hasattr(User, '__dataclass_fields__') else []:
        if field not in ignore_fields:
            assert getattr(user1, field) == getattr(user2, field), f"Field {field} differs"


def assert_post_equal(post1: Post, post2: Post, ignore_fields: list[str] | None = None):
    """
    Assert two Post instances are equal, ignoring specified fields.

    Args:
        post1: First Post instance
        post2: Second Post instance
        ignore_fields: List of field names to ignore in comparison
    """
    if ignore_fields is None:
        ignore_fields = []

    for field in Post.__dataclass_fields__ if hasattr(Post, '__dataclass_fields__') else []:
        if field not in ignore_fields:
            assert getattr(post1, field) == getattr(post2, field), f"Field {field} differs"


# =============================================================================
# Pytest Marks for Repository Tests
# =============================================================================

# Mark for tests that require database
requires_db = pytest.mark.requires_db

# Mark for tests that test transactional behavior
transactional = pytest.mark.transactional

# Mark for integration tests
integration = pytest.mark.integration
