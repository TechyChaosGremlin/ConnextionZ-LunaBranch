"""Allow profile avatar data URLs.

Revision ID: 20260816_0002
Revises: 20260816_0001
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0002"
down_revision: Union[str, None] = "20260816_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column(
            "avatar_url",
            existing_type=sa.String(length=500),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column(
            "avatar_url",
            existing_type=sa.Text(),
            type_=sa.String(length=500),
            existing_nullable=True,
        )
