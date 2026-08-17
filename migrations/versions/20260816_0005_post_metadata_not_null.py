"""Finalize post metadata constraints.

Revision ID: 20260816_0005
Revises: 20260816_0004
Create Date: 2026-08-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0005"
down_revision: Union[str, None] = "20260816_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.alter_column("hashtags", existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column("audio", existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("visibility", existing_type=sa.String(length=20), nullable=False)
        batch_op.alter_column("allow_comments", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column("allow_collabs", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column("duration_sec", existing_type=sa.Float(), nullable=False)
        batch_op.alter_column("comments", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("shares", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("saves", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        for column in (
            "hashtags", "audio", "visibility", "allow_comments", "allow_collabs",
            "duration_sec", "comments", "shares", "saves",
        ):
            batch_op.alter_column(column, nullable=True)
