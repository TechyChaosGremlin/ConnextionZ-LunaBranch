"""
SQLAlchemy declarative base and shared model utilities.

All models inherit from :class:`Base` which provides:
- UUIDv7 primary key generation
- Automatic ``created_at`` / ``updated_at`` timestamps
- Soft-delete support via ``deleted_at``
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


def generate_uuidv7() -> uuid.UUID:
    """Generate a time-sortable UUIDv7.

    UUIDv7 encodes a Unix timestamp (ms) in the first 48 bits, making
    primary keys naturally ordered by creation time — ideal for B-tree
    indexes and cursor-based pagination.
    """
    import time as _time

    # Build a UUIDv7 from scratch per RFC 9562
    timestamp_ms = int(_time.time() * 1000)
    rand_bytes = uuid.uuid4().bytes

    # Timestamp occupies bytes 0-5 (48 bits, big-endian)
    ts_bytes = timestamp_ms.to_bytes(6, "big")

    # Construct: timestamp (6) + version/variant + random (10)
    raw = bytearray(16)
    raw[0:6] = ts_bytes
    raw[6:16] = rand_bytes[6:16]

    # Set version to 7 (byte 6, high nibble)
    raw[6] = (raw[6] & 0x0F) | 0x70
    # Set variant to 10xx (byte 8, high nibble)
    raw[8] = (raw[8] & 0x3F) | 0x80

    return uuid.UUID(bytes=bytes(raw))


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` columns.

    ``created_at`` is set once on INSERT and never changes.
    ``updated_at`` is set on INSERT and updated on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin that adds a ``deleted_at`` column for soft-delete support.

    Rows with ``deleted_at IS NOT NULL`` are considered deleted.
    Queries should filter ``deleted_at IS NULL`` to exclude soft-deleted rows.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""

    # All tables use UUIDv7 primary keys
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuidv7,
        sort_order=-1,  # Always first column
    )

    def __repr__(self) -> str:
        cls = type(self).__name__
        return f"<{cls} id={self.id!r}>"