"""Concurrency regression tests for post save mutations."""

import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from backend.app.main import Mutation
from backend.app.models import Base, Post, PostSave, Profile, User


class SaveMutationTests(unittest.TestCase):
    def test_concurrent_saves_from_one_user_are_idempotent(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "saves.db"
            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False, "timeout": 10},
            )
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                user = User(email="race-user@example.test")
                session.add(user)
                session.flush()
                profile = Profile(
                    user_id=user.id,
                    username="race-user",
                    display_name="Race User",
                )
                post = Post(
                    profile=profile,
                    thumbnail="/media/post.jpg",
                    saves=0,
                )
                session.add(post)
                session.commit()
                user_id = user.id
                post_id = post.id

            read_barrier = threading.Barrier(2)
            synchronized_reads = 0
            read_lock = threading.Lock()

            @event.listens_for(engine, "before_cursor_execute")
            def synchronize_save_reads(connection, cursor, statement, parameters, context, executemany):
                nonlocal synchronized_reads
                normalized = statement.strip().upper()
                if normalized.startswith("SELECT") and "FROM POST_SAVES" in normalized:
                    with read_lock:
                        synchronized_reads += 1
                        should_wait = synchronized_reads <= 2
                    if should_wait:
                        read_barrier.wait(timeout=10)

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": user_id})

            def save_post() -> object:
                return Mutation().save_post(str(post_id), info)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        results = list(executor.map(lambda _: save_post(), range(2)))

                with Session(engine) as session:
                    stored_post = session.get(Post, post_id)
                    stored_saves = session.scalars(
                        select(PostSave).where(PostSave.post_id == post_id, PostSave.user_id == user_id)
                    ).all()
            finally:
                event.remove(engine, "before_cursor_execute", synchronize_save_reads)
                engine.dispose()

            self.assertTrue(all(result.saved for result in results))
            self.assertEqual(stored_post.saves, 1)
            self.assertEqual(len(stored_saves), 1)

    def test_unsave_removes_the_record_and_resyncs_the_count(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "saves.db"
            engine = create_engine(f"sqlite:///{database_path}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                user = User(email="saver@example.test")
                session.add(user)
                session.flush()
                profile = Profile(user_id=user.id, username="saver", display_name="Saver")
                post = Post(profile=profile, thumbnail="/media/post.jpg", saves=0)
                session.add(post)
                session.commit()
                user_id = user.id
                post_id = post.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": user_id})

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    saved = Mutation().save_post(str(post_id), info)
                    unsaved = Mutation().unsave_post(str(post_id), info)
                    # Unsaving twice must not push the counter negative.
                    unsaved_again = Mutation().unsave_post(str(post_id), info)

                with Session(engine) as session:
                    stored_post = session.get(Post, post_id)
                    stored_saves = session.scalars(
                        select(PostSave).where(PostSave.post_id == post_id)
                    ).all()
            finally:
                engine.dispose()

            self.assertTrue(saved.saved)
            self.assertEqual(saved.saves, 1)
            self.assertFalse(unsaved.saved)
            self.assertEqual(unsaved.saves, 0)
            self.assertEqual(unsaved_again.saves, 0)
            self.assertEqual(stored_post.saves, 0)
            self.assertEqual(len(stored_saves), 0)

    def test_save_requires_authentication(self) -> None:
        info = SimpleNamespace(context={})
        with self.assertRaises(Exception):
            Mutation().save_post("1", info)


if __name__ == "__main__":
    unittest.main()
