"""Concurrency regression tests for post like mutations."""

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
from backend.app.models import Base, Post, PostLike, Profile, User


class LikeMutationConcurrencyTests(unittest.TestCase):
    def test_concurrent_likes_from_one_user_are_idempotent(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "likes.db"
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
                    likes=0,
                )
                session.add(post)
                session.commit()
                user_id = user.id
                post_id = post.id

            read_barrier = threading.Barrier(2)
            synchronized_reads = 0
            read_lock = threading.Lock()

            @event.listens_for(engine, "before_cursor_execute")
            def synchronize_like_reads(connection, cursor, statement, parameters, context, executemany):
                nonlocal synchronized_reads
                normalized = statement.strip().upper()
                if normalized.startswith("SELECT") and "FROM POST_LIKES" in normalized:
                    with read_lock:
                        synchronized_reads += 1
                        should_wait = synchronized_reads <= 2
                    if should_wait:
                        read_barrier.wait(timeout=10)

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": user_id})

            def like_post() -> object:
                return Mutation().like_post(str(post_id), info)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        results = list(executor.map(lambda _: like_post(), range(2)))

                with Session(engine) as session:
                    saved_post = session.get(Post, post_id)
                    saved_likes = session.scalars(
                        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
                    ).all()
            finally:
                event.remove(engine, "before_cursor_execute", synchronize_like_reads)
                engine.dispose()

            self.assertTrue(all(result.liked for result in results))
            self.assertEqual(saved_post.likes, 1)
            self.assertEqual(len(saved_likes), 1)

    def test_concurrent_likes_from_different_users_are_counted(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "likes.db"
            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False, "timeout": 10},
            )
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                user_one = User(email="user-one@example.test")
                user_two = User(email="user-two@example.test")
                session.add_all([user_one, user_two])
                session.flush()
                profile = Profile(
                    user_id=user_one.id,
                    username="profile-owner",
                    display_name="Profile Owner",
                )
                post = Post(
                    profile=profile,
                    thumbnail="/media/post.jpg",
                    likes=0,
                )
                session.add(post)
                session.commit()
                user_ids = [user_one.id, user_two.id]
                post_id = post.id

            read_barrier = threading.Barrier(2)
            synchronized_reads = 0
            read_lock = threading.Lock()

            @event.listens_for(engine, "before_cursor_execute")
            def synchronize_like_reads(connection, cursor, statement, parameters, context, executemany):
                nonlocal synchronized_reads
                normalized = statement.strip().upper()
                if normalized.startswith("SELECT") and "FROM POST_LIKES" in normalized:
                    with read_lock:
                        synchronized_reads += 1
                        should_wait = synchronized_reads <= 2
                    if should_wait:
                        read_barrier.wait(timeout=10)

            def get_test_session() -> Session:
                return Session(engine)

            def like_post(user_id: int) -> object:
                info = SimpleNamespace(context={"user_id": user_id})
                return Mutation().like_post(str(post_id), info)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        results = list(executor.map(like_post, user_ids))

                with Session(engine) as session:
                    saved_post = session.get(Post, post_id)
                    saved_likes = session.scalars(
                        select(PostLike).where(PostLike.post_id == post_id)
                    ).all()
            finally:
                event.remove(engine, "before_cursor_execute", synchronize_like_reads)
                engine.dispose()

            self.assertTrue(all(result.liked for result in results))
            self.assertEqual(saved_post.likes, 2)
            self.assertEqual(len(saved_likes), 2)


if __name__ == "__main__":
    unittest.main()