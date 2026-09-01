from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import async_session_factory
from app.models.messaging import Conversation, ConversationParticipant, Message
from app.models.social import UserBlock
from app.models.user import AccountStatus, User, UserRole
from repositories.messaging_repository import ConversationRepository, MessageRepository


@pytest.mark.asyncio
async def test_messaging_repository_flow_uses_postgresql_constraints():
    async with async_session_factory() as session:
        transaction = await session.begin()
        try:
            now = datetime.now(timezone.utc)
            sender = User(
                email="messaging-sender@example.test",
                username="messaging_sender",
                hashed_password="hashed",
                role=UserRole.USER,
                status=AccountStatus.ACTIVE,
                email_verified=True,
                mfa_enabled=False,
            )
            recipient = User(
                email="messaging-recipient@example.test",
                username="messaging_recipient",
                hashed_password="hashed",
                role=UserRole.USER,
                status=AccountStatus.ACTIVE,
                email_verified=True,
                mfa_enabled=False,
            )
            session.add_all([sender, recipient])
            await session.flush()

            conversation = Conversation(last_message_at=now.isoformat())
            session.add(conversation)
            await session.flush()
            session.add_all(
                [
                    ConversationParticipant(
                        conversation_id=conversation.id, user_id=sender.id
                    ),
                    ConversationParticipant(
                        conversation_id=conversation.id, user_id=recipient.id
                    ),
                ]
            )
            await session.flush()

            conversation_repo = ConversationRepository(session)
            message_repo = MessageRepository(session)
            assert await conversation_repo.get_participant(conversation.id, sender.id)
            assert await conversation_repo.get_active_user_ids([sender.id, recipient.id]) == [
                sender.id,
                recipient.id,
            ]

            first_message = Message(
                conversation_id=conversation.id,
                sender_id=sender.id,
                body="first",
                content_type="text",
                client_message_id="message-1",
                created_at=now - timedelta(seconds=1),
                updated_at=now - timedelta(seconds=1),
            )
            second_message = Message(
                conversation_id=conversation.id,
                sender_id=sender.id,
                body="second",
                content_type="text",
                client_message_id="message-2",
                created_at=now,
                updated_at=now,
            )
            session.add_all([first_message, second_message])
            await session.flush()

            messages = await message_repo.get_for_conversation(conversation.id, limit=1)
            assert [message.id for message in messages] == [second_message.id]
            next_page = await message_repo.get_for_conversation(
                conversation.id, limit=1, before=(second_message.created_at, second_message.id)
            )
            assert [message.id for message in next_page] == [first_message.id]
            assert await message_repo.get_unread_count(recipient.id) == 2

            recipient_participant = await conversation_repo.get_participant(
                conversation.id, recipient.id
            )
            await message_repo.mark_conversation_read(recipient_participant)
            assert await message_repo.get_unread_count(recipient.id) == 0

            duplicate = Message(
                conversation_id=conversation.id,
                sender_id=sender.id,
                body="duplicate",
                content_type="text",
                client_message_id="message-1",
            )
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    session.add(duplicate)
                    await session.flush()

            await message_repo.soft_delete(first_message)
            assert await message_repo.get_for_conversation(conversation.id, limit=10) == [
                second_message
            ]

            session.add(UserBlock(blocker_id=recipient.id, blocked_id=sender.id))
            await session.flush()
            assert await conversation_repo.users_are_blocked(sender.id, [recipient.id])
        finally:
            await transaction.rollback()
