"""Add persisted trending sounds.

Revision ID: 20260817_0006
Revises: 20260816_0005
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260817_0006"
down_revision: Union[str, None] = "20260816_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sounds",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("creator", sa.String(length=120), nullable=False),
        sa.Column("creator_avatar", sa.Text(), nullable=False),
        sa.Column("artwork", sa.Text(), nullable=False),
        sa.Column("genre", sa.String(length=80), nullable=False),
        sa.Column("video_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_plays", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("growth_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration", sa.String(length=20), nullable=False, server_default="0:30"),
        sa.Column("bpm", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_sounds_genre", "sounds", ["genre"])

    sounds = sa.table(
        "sounds",
        sa.column("id", sa.String), sa.column("title", sa.String),
        sa.column("creator", sa.String), sa.column("creator_avatar", sa.Text),
        sa.column("artwork", sa.Text), sa.column("genre", sa.String),
        sa.column("video_count", sa.Integer), sa.column("total_plays", sa.Integer),
        sa.column("rank", sa.Integer), sa.column("growth_pct", sa.Integer),
        sa.column("duration", sa.String), sa.column("bpm", sa.Integer),
    )
    op.bulk_insert(sounds, [
        {"id": "s1", "title": "Midnight Drive", "creator": "nova.dj", "creator_avatar": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=60&h=60&fit=crop&auto=format", "artwork": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop&auto=format", "genre": "Electronic", "video_count": 284700, "total_plays": 18400000, "rank": 1, "growth_pct": 142, "duration": "0:45", "bpm": 128},
        {"id": "s2", "title": "golden hour", "creator": "JVKE", "creator_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=60&h=60&fit=crop&auto=format", "artwork": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop&auto=format", "genre": "Pop", "video_count": 531200, "total_plays": 42100000, "rank": 2, "growth_pct": 89, "duration": "0:30", "bpm": 95},
        {"id": "s3", "title": "HYPERSONIC", "creator": "nova.dj", "creator_avatar": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=60&h=60&fit=crop&auto=format", "artwork": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&h=300&fit=crop&auto=format", "genre": "Electronic", "video_count": 892400, "total_plays": 67300000, "rank": 3, "growth_pct": 67, "duration": "1:00", "bpm": 140},
    ])


def downgrade() -> None:
    op.drop_index("ix_sounds_genre", table_name="sounds")
    op.drop_table("sounds")
