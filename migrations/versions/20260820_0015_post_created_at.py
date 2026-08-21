"""Add creation timestamps for feed freshness ranking.

Revision ID: 20260820_0015
Revises: 20260820_0014
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0015"
down_revision: Union[str, None] = "20260820_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("posts")}
    if "created_at" in columns:
        return
    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_posts_created_at", ["created_at"], unique=False)
    op.execute(sa.text("UPDATE posts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("posts")}
    if "created_at" not in columns:
        return
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_index("ix_posts_created_at")
        batch_op.drop_column("created_at")