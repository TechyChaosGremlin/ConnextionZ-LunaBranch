"""Add scheduled post timestamps.

Revision ID: 20260820_0014
Revises: 20260820_0013
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0014"
down_revision: Union[str, None] = "20260820_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("posts")}
    if "scheduled_at" in columns:
        return
    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_posts_scheduled_at", ["scheduled_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("posts")}
    if "scheduled_at" not in columns:
        return
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_index("ix_posts_scheduled_at")
        batch_op.drop_column("scheduled_at")
