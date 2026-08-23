"""
Messaging repository for database operations.

Provides CRUD operations for Conversation and Message models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messaging import (
    Conversation, ConversationParticipant, Message,
    MessageType, MessageStatus,
)
from repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model database operations.

    Extends BaseRepository with common CRUD operations and adds
    conversation-specific methods for participants and user lookups.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Conversation)

    async def get_for_user(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[Conversation]:
        """Get conversations where user is a participant."""
        # Subquery to find conversation IDs where user is a participant
        participant_conv_ids = select(ConversationParticipant.conversation_id).where(
            ConversationParticipant.user_id == user_id
        ).subquery()

        stmt = select(Conversation).where(
            Conversation.id.in_(participant_conv_ids)
        )
        if before_id:
            stmt = stmt.where(Conversation.id < before_id)
        stmt = stmt.order_by(Conversation.last_message_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_participant(
        self, participant: ConversationParticipant
    ) -> ConversationParticipant:
        """Add a participant to a conversation."""
        self.db.add(participant)
        await self.db.flush()
        await self.db.refresh(participant)
        return participant

    async def get_participant(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ConversationParticipant]:
        """Get a specific participant in a conversation."""
        result = await self.db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model database operations.

    Extends BaseRepository with common CRUD operations and adds
    message-specific methods for conversation and status management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        super().__init__(db, Message)

    async def get_for_conversation(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[Message]:
        """Get messages for a conversation."""
        stmt = select(Message).where(
            Message.conversation_id == conversation_id
        )
        if before_id:
            stmt = stmt.where(Message.id < before_id)
        stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, message: Message, status: MessageStatus
    ) -> Message:
        """Update message status."""
        message.status = status
        await self.db.flush()
        await self.db.refresh(message)
        return message
