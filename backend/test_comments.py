"""Regression tests for persistent comment operations."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.main import Mutation, Query
from backend.app.models import Base, Post, Profile, User


class CommentTests(unittest.TestCase):
    def test_comment_lifecycle_and_like_state(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'comments.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                author = User(email="author@example.test")
                commenter = User(email="commenter@example.test")
                session.add_all([author, commenter])
                session.flush()
                profile = Profile(user_id=author.id, username="author", display_name="Author")
                commenter_profile = Profile(user_id=commenter.id, username="commenter", display_name="Commenter")
                post = Post(profile=profile, thumbnail="/post.jpg")
                session.add_all([commenter_profile, post])
                session.commit()
                post_id = post.id
                commenter_id = commenter.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": commenter_id})
            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    created = Mutation().add_comment(str(post_id), "Hello from the backend", info)
                    self.assertEqual(created.text, "Hello from the backend")
                    self.assertTrue(created.can_delete)

                    comments = Query().comments(str(post_id), info)
                    self.assertEqual(len(comments), 1)
                    self.assertEqual(comments[0].id, created.id)

                    liked = Mutation().like_comment(created.id, info)
                    self.assertTrue(liked.liked)
                    self.assertEqual(liked.likes, 1)
                    unliked = Mutation().unlike_comment(created.id, info)
                    self.assertFalse(unliked.liked)
                    self.assertEqual(unliked.likes, 0)

                    self.assertTrue(Mutation().delete_comment(created.id, info))
                    self.assertEqual(Query().comments(str(post_id), info), [])
                    with Session(engine) as session:
                        self.assertEqual(session.scalar(select(Post.comments).where(Post.id == post_id)), 0)
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
