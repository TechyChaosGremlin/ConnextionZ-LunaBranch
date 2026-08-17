"""Store durable URLs for uploaded post media.

Revision ID: 20260816_0003
Revises: 20260816_0002
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0003"
down_revision: Union[str, None] = "20260816_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("media_url", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_column("media_url")
