"""Add private account flag to profiles.

Revision ID: 20260819_0009
Revises: 20260818_0008
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260819_0009"
down_revision: Union[str, None] = "20260818_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("profiles")}

    if "private_account" not in columns:
        with op.batch_alter_table("profiles") as batch:
            batch.add_column(
                sa.Column(
                    "private_account",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("profiles")}

    if "private_account" in columns:
        with op.batch_alter_table("profiles") as batch:
            batch.drop_column("private_account")
