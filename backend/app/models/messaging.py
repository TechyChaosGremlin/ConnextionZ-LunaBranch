"""
Messaging models — conversations and messages.

Covers the Direct Messaging feature.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


# ── Conversation ─────────────────────────────────────────────────


class Conversation(Base, TimestampMixin, SoftDeleteMixin):
    """A conversation thread between two or more users."""

    __tablename__ = "conversations"

    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Last message preview (denormalized)
    last_message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_message_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Relationships
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id!r} group={self.is_group!r}>"


# ── ConversationParticipant ──────────────────────────────────────


class ConversationParticipant(Base, TimestampMixin):
    """Join table linking users to conversations."""

    __tablename__ = "conversation_participants"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conversation_participant"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Participant state
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_read_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="participants"
    )

    def __repr__(self) -> str:
        return f"<ConversationParticipant conv={self.conversation_id!r} user={self.user_id!r}>"


# ── Message ──────────────────────────────────────────────────────


class Message(Base, TimestampMixin, SoftDeleteMixin):
    """A single message within a conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id", "sender_id", "client_message_id",
            name="uq_message_idempotency_key",
        ),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content
    body: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(32), default="text", nullable=False
    )  # "text", "image", "file", "collaboration_invite"

    # Attachments
    attachments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    client_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Status
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id!r} conv={self.conversation_id!r} sender={self.sender_id!r}>"