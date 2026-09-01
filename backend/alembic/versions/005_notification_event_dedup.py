"""Enforce one delivery for each notification event.

Revision ID: 005
Revises: 004
Create Date: 2026-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("event_key", sa.String(256), nullable=True))
    op.create_unique_constraint(
        "uq_notification_event_delivery",
        "notifications",
        ["user_id", "type", "actor_id", "event_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_notification_event_delivery", "notifications", type_="unique")
    op.drop_column("notifications", "event_key")