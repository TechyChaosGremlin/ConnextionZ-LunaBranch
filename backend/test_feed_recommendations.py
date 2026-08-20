"""Regression tests for For You feed ranking."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.main import Query
from backend.app.models import Base, Post, Profile, User


class FeedRecommendationTests(unittest.TestCase):
    def test_for_you_ranks_engagement_above_post_id(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'feed.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                creator = User(email="creator@example.test")
                viewer = User(email="viewer@example.test")
                session.add_all([creator, viewer])
                session.flush()
                profile = Profile(
                    user_id=creator.id,
                    username="creator",
                    display_name="Creator",
                )
                popular_post = Post(profile=profile, thumbnail="/popular.jpg", likes=100)
                newer_post = Post(profile=profile, thumbnail="/newer.jpg", likes=0)
                session.add_all([popular_post, newer_post])
                session.commit()
                popular_id = popular_post.id
                viewer_id = viewer.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": viewer_id})
            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    page = Query().feed(info, limit=10, following=False)
            finally:
                engine.dispose()

            self.assertEqual(page.items[0].id, str(popular_id))


if __name__ == "__main__":
    unittest.main()