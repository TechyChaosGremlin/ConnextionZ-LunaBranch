"""
Database session dependency for FastAPI.

Provides async database session injection for route handlers.
"""

from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that provides an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for FastAPI dependency
AsyncSessionDep = Depends(get_db_session)
