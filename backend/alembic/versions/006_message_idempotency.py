"""Add an idempotency key for retried message submissions.

Revision ID: 006
Revises: 005
Create Date: 2026-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("client_message_id", sa.String(128), nullable=True))
    op.create_unique_constraint(
        "uq_message_idempotency_key",
        "messages",
        ["conversation_id", "sender_id", "client_message_id"],
    )
    op.create_unique_constraint(
        "uq_conversation_participant",
        "conversation_participants",
        ["conversation_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_conversation_participant", "conversation_participants", type_="unique")
    op.drop_constraint("uq_message_idempotency_key", "messages", type_="unique")
    op.drop_column("messages", "client_message_id")
