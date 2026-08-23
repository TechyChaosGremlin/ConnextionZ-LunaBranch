from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session

from app.models import Base

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "profiles.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    existing_tables = set(inspect(engine).get_table_names())
    required_tables = {"users", "profiles", "follows", "user_blocks", "user_mutes", "posts", "post_likes", "post_saves", "post_shares", "post_watches", "post_reports", "comments", "comment_likes", "comment_reports", "notifications", "playlists", "search_queries"}
    if required_tables.issubset(existing_tables) and "alembic_version" not in existing_tables:
        command.stamp(config, "head")
    command.upgrade(config, "head")


def get_session() -> Session:
    return Session(engine)
