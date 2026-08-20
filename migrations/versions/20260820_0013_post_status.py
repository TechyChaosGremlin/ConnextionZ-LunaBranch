"""Add post draft status.

Revision ID: 20260820_0013
Revises: 20260820_0012
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0013"
down_revision: Union[str, None] = "20260820_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("posts")}
    if "status" in columns:
        return

    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=True))
    op.execute("UPDATE posts SET status = 'published' WHERE status IS NULL")
    with op.batch_alter_table("posts") as batch_op:
        batch_op.alter_column("status", existing_type=sa.String(length=20), nullable=False)
        batch_op.create_index("ix_posts_status", ["status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("posts")}
    if "status" not in columns:
        return

    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_index("ix_posts_status")
        batch_op.drop_column("status")