"""Track post views and watch behavior.

Revision ID: 20260820_0017
Revises: 20260820_0016
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0017"
down_revision: Union[str, None] = "20260820_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if "post_watches" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "post_watches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("watched_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rewatched", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_post_watches_id", "post_watches", ["id"])
    op.create_index("ix_post_watches_post_id", "post_watches", ["post_id"])
    op.create_index("ix_post_watches_user_id", "post_watches", ["user_id"])
    op.create_index("ix_post_watches_created_at", "post_watches", ["created_at"])


def downgrade() -> None:
    op.drop_table("post_watches")