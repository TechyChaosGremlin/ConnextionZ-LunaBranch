from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.graphql import (
    _conversation,
    _conversations,
    _create_conversation,
    _mark_conversation_read,
    _messages,
    _send_message,
    _unread_conversation_count,
)
from app.models.messaging import Conversation, Message


class FakeConversationRepository:
    existing = None
    blocked = False
    active_user_ids = None
    participant = SimpleNamespace(last_read_at=None)
    conversation = None
    last_conversation_cursor = None
    last_message_cursor = None

    def __init__(self, db):
        self.db = db

    async def users_are_blocked(self, user_id, participant_ids):
        return self.blocked

    async def get_direct_conversation(self, user_id, participant_id):
        return self.existing

    async def create(self, conversation):
        conversation.id = uuid4()
        return conversation

    async def add_participant(self, participant):
        return participant

    async def get_participant(self, conversation_id, user_id):
        return self.participant

    async def get_participant_ids(self, conversation_id):
        return [self.db.user_id, uuid4()]

    async def get_active_user_ids(self, user_ids):
        return user_ids if self.active_user_ids is None else self.active_user_ids

    async def get_for_user(self, user_id, limit, before):
        self.__class__.last_conversation_cursor = before
        return []

    async def count_for_user(self, user_id):
        return 0

    async def get_notification_recipient_ids(self, conversation_id, sender_id):
        return []

    async def get_by_id(self, conversation_id):
        return self.conversation


class FakeMessageRepository:
    existing = None
    created = []
    unread_count = 0

    def __init__(self, db):
        self.db = db

    async def get_by_client_message_id(self, conversation_id, sender_id, client_message_id):
        return self.existing

    async def get_for_conversation(self, conversation_id, limit, before):
        FakeConversationRepository.last_message_cursor = before
        return []

    async def count_for_conversation(self, conversation_id):
        return 0

    async def create(self, message):
        message.id = uuid4()
        self.created.append(message)
        return message

    async def mark_conversation_read(self, participant):
        participant.last_read_at = datetime.now(timezone.utc).isoformat()
        return participant

    async def get_unread_count(self, user_id):
        return self.unread_count


def messaging_context():
    user = SimpleNamespace(
        id=uuid4(),
        username="sender",
        status=SimpleNamespace(value="active"),
        deleted_at=None,
    )
    return SimpleNamespace(
        user=user,
        db=SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock()),
        require_auth=lambda: user,
    )


@pytest.fixture(autouse=True)
def fake_messaging_repositories(monkeypatch):
    FakeConversationRepository.existing = None
    FakeConversationRepository.blocked = False
    FakeConversationRepository.active_user_ids = None
    FakeConversationRepository.participant = SimpleNamespace(last_read_at=None)
    FakeConversationRepository.conversation = Conversation(id=uuid4(), is_group=False)
    FakeConversationRepository.last_conversation_cursor = None
    FakeConversationRepository.last_message_cursor = None
    FakeMessageRepository.existing = None
    FakeMessageRepository.created = []
    FakeMessageRepository.unread_count = 0
    monkeypatch.setattr("repositories.messaging_repository.ConversationRepository", FakeConversationRepository)
    monkeypatch.setattr("repositories.messaging_repository.MessageRepository", FakeMessageRepository)


@pytest.mark.asyncio
async def test_create_conversation_reuses_existing_direct_thread():
    ctx = messaging_context()
    existing = Conversation(id=uuid4(), is_group=False, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    FakeConversationRepository.existing = existing
    input = SimpleNamespace(participant_ids=[uuid4()], title=None, initial_message=None)

    result = await _create_conversation(ctx, input)

    assert result.id == existing.id
    assert ctx.db.commit.await_count == 0


@pytest.mark.asyncio
async def test_conversation_requires_active_participant_membership():
    ctx = messaging_context()
    conversation = FakeConversationRepository.conversation

    result = await _conversation(ctx, conversation.id)
    assert result.id == conversation.id

    FakeConversationRepository.participant = None
    with pytest.raises(ValueError, match="Access denied"):
        await _conversation(ctx, conversation.id)


@pytest.mark.asyncio
async def test_send_message_uses_declared_input_and_idempotency(monkeypatch):
    ctx = messaging_context()
    ctx.db.user_id = ctx.user.id
    conversation_id = uuid4()
    input = SimpleNamespace(
        conversation_id=conversation_id,
        body="  hello  ",
        content_type="text",
        attachments={"url": "https://example.test/file"},
        client_message_id="retry-1",
    )
    monkeypatch.setattr("api.graphql._notify", AsyncMock())

    result = await _send_message(ctx, input)

    assert result.body == "hello"
    assert result.attachments == {"url": "https://example.test/file"}
    assert FakeMessageRepository.created[0].client_message_id == "retry-1"
    assert FakeConversationRepository.conversation.last_message_text == "hello"
    assert ctx.db.commit.await_count == 1


@pytest.mark.asyncio
async def test_send_message_rejects_invalid_or_blocked_messages(monkeypatch):
    ctx = messaging_context()
    ctx.db.user_id = ctx.user.id
    input = SimpleNamespace(
        conversation_id=uuid4(), body=" ", content_type="text", attachments=None, client_message_id=None
    )

    with pytest.raises(ValueError, match="Message body"):
        await _send_message(ctx, input)

    input.body = "hello"
    FakeConversationRepository.blocked = True
    with pytest.raises(PermissionError, match="blocked"):
        await _send_message(ctx, input)


@pytest.mark.asyncio
async def test_read_and_unread_operations_use_participant_membership():
    ctx = messaging_context()
    ctx.require_auth = lambda: ctx.user
    FakeMessageRepository.unread_count = 3

    assert await _mark_conversation_read(ctx, uuid4()) is True
    assert FakeConversationRepository.participant.last_read_at is not None
    assert await _unread_conversation_count(ctx) == 3


@pytest.mark.asyncio
async def test_messaging_rejects_inactive_accounts_and_unavailable_participants():
    ctx = messaging_context()
    ctx.user.status.value = "suspended"
    input = SimpleNamespace(participant_ids=[uuid4()], title=None, initial_message=None)

    with pytest.raises(PermissionError, match="not active"):
        await _create_conversation(ctx, input)

    ctx.user.status.value = "active"
    FakeConversationRepository.active_user_ids = []
    with pytest.raises(ValueError, match="recipients are unavailable"):
        await _create_conversation(ctx, input)

    FakeConversationRepository.active_user_ids = None
    input.initial_message = " "
    ctx.db.rollback.reset_mock()
    with pytest.raises(ValueError, match="Initial message"):
        await _create_conversation(ctx, input)
    assert ctx.db.rollback.await_count == 1

    ctx.user.deleted_at = datetime.now(timezone.utc)
    with pytest.raises(PermissionError, match="not active"):
        await _create_conversation(ctx, input)


@pytest.mark.asyncio
async def test_message_access_and_database_failures_are_handled(monkeypatch):
    ctx = messaging_context()
    ctx.db.user_id = ctx.user.id
    input = SimpleNamespace(
        conversation_id=uuid4(), body="hello", content_type="text", attachments=None,
        client_message_id=None,
    )
    FakeConversationRepository.participant = None
    with pytest.raises(ValueError, match="Access denied"):
        await _send_message(ctx, input)

    FakeConversationRepository.participant = SimpleNamespace(last_read_at=None)
    ctx.db.rollback = AsyncMock()
    monkeypatch.setattr(FakeMessageRepository, "create", AsyncMock(side_effect=SQLAlchemyError()))
    with pytest.raises(ValueError, match="Messaging operation failed"):
        await _send_message(ctx, input)
    assert ctx.db.rollback.await_count == 1


@pytest.mark.asyncio
async def test_send_message_recovers_idempotency_constraint_race(monkeypatch):
    ctx = messaging_context()
    ctx.db.user_id = ctx.user.id
    conversation_id = uuid4()
    existing = Message(
        id=uuid4(),
        conversation_id=conversation_id,
        sender_id=ctx.user.id,
        body="hello",
        content_type="text",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    input = SimpleNamespace(
        conversation_id=conversation_id,
        body="hello",
        content_type="text",
        attachments=None,
        client_message_id="retry-1",
    )
    FakeMessageRepository.existing = None
    monkeypatch.setattr(
        FakeMessageRepository,
        "create",
        AsyncMock(side_effect=IntegrityError(None, None, Exception("duplicate"))),
    )

    lookup_count = 0

    async def find_message(self, conversation_id, sender_id, client_message_id):
        nonlocal lookup_count
        lookup_count += 1
        return None if lookup_count == 1 else existing

    monkeypatch.setattr(FakeMessageRepository, "get_by_client_message_id", find_message)
    result = await _send_message(ctx, input)

    assert result.id == existing.id
    assert ctx.db.rollback.await_count == 1


@pytest.mark.asyncio
async def test_message_and_conversation_cursors_include_ordering_timestamp():
    ctx = messaging_context()
    conversation_id = uuid4()
    timestamp = datetime.now(timezone.utc).isoformat()

    await _conversations(ctx, 1, f"{timestamp}|{conversation_id}")
    await _messages(ctx, conversation_id, 1, f"{timestamp}|{conversation_id}")

    assert FakeConversationRepository.last_conversation_cursor == (timestamp, conversation_id)
    assert FakeConversationRepository.last_message_cursor == (datetime.fromisoformat(timestamp), conversation_id)
