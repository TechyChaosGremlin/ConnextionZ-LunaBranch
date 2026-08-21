"""Regression tests for view and watch tracking."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.main import Mutation, Query
from backend.app.models import Base, Post, PostWatch, Profile, User


class WatchTrackingTests(unittest.TestCase):
    def test_first_watch_counts_view_and_rewatch_does_not(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'watch.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                creator = User(email="creator@example.test")
                viewer = User(email="viewer@example.test")
                session.add_all([creator, viewer])
                session.flush()
                profile = Profile(user_id=creator.id, username="creator", display_name="Creator")
                post = Post(profile=profile, thumbnail="/post.jpg", duration_sec=30)
                session.add(post)
                session.commit()
                post_id = post.id
                viewer_id = viewer.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": viewer_id})
            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    first = Mutation().track_post_watch(
                        post_id=str(post_id), watched_seconds=30, completed=True, info=info,
                    )
                    second = Mutation().track_post_watch(
                        post_id=str(post_id), watched_seconds=12, completed=False, info=info,
                    )
                with Session(engine) as session:
                    post = session.get(Post, post_id)
                    events = session.scalars(select(PostWatch)).all()
                    self.assertEqual(post.views, 1)
                    self.assertEqual(len(events), 2)
                    self.assertTrue(events[0].completed)
                    self.assertTrue(events[1].rewatched)
            finally:
                engine.dispose()

            self.assertEqual(first.views, 1)
            self.assertFalse(first.rewatched)
            self.assertTrue(second.rewatched)

    def test_completed_watch_influences_for_you_creator_affinity(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'feed.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                creator_a = User(email="creator-a@example.test")
                creator_b = User(email="creator-b@example.test")
                viewer = User(email="viewer@example.test")
                session.add_all([creator_a, creator_b, viewer])
                session.flush()
                profile_a = Profile(user_id=creator_a.id, username="creator_a", display_name="Creator A")
                profile_b = Profile(user_id=creator_b.id, username="creator_b", display_name="Creator B")
                watched = Post(profile=profile_a, thumbnail="/watched.jpg")
                related = Post(profile=profile_a, thumbnail="/related.jpg")
                unrelated = Post(profile=profile_b, thumbnail="/unrelated.jpg")
                session.add_all([watched, related, unrelated])
                session.flush()
                session.add(PostWatch(post_id=watched.id, user_id=viewer.id, watched_seconds=10, completed=True))
                session.commit()
                related_id = related.id
                viewer_id = viewer.id

            def get_test_session() -> Session:
                return Session(engine)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    page = Query().feed(SimpleNamespace(context={"user_id": viewer_id}), limit=3, following=False)
            finally:
                engine.dispose()

            self.assertEqual(page.items[0].id, str(related_id))


if __name__ == "__main__":
    unittest.main()
