"""Regression tests for post share mutations."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.main import Mutation, post_to_graphql
from backend.app.models import Base, Post, PostShare, Profile, User


class ShareMutationTests(unittest.TestCase):
    def test_share_tracks_the_viewer_and_is_idempotent(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'shares.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                user = User(email="sharer@example.test")
                session.add(user)
                session.flush()
                profile = Profile(user_id=user.id, username="sharer", display_name="Sharer")
                post = Post(profile=profile, thumbnail="/media/post.jpg", shares=0)
                session.add(post)
                session.commit()
                user_id = user.id
                post_id = post.id

            info = SimpleNamespace(context={"user_id": user_id})

            try:
                with patch("backend.app.main.get_session", side_effect=lambda: Session(engine)):
                    first = Mutation().share_post(str(post_id), info)
                    second = Mutation().share_post(str(post_id), info)

                with Session(engine) as session:
                    stored_post = session.get(Post, post_id)
                    stored_shares = session.query(PostShare).filter_by(post_id=post_id, user_id=user_id).all()
                    serialized_post = post_to_graphql(
                        stored_post,
                        viewer_id=user_id,
                        shared_post_ids={share.post_id for share in stored_shares},
                    )
            finally:
                engine.dispose()

            self.assertEqual(first.shares, 1)
            self.assertTrue(first.shared)
            self.assertEqual(second.shares, 1)
            self.assertTrue(second.shared)
            self.assertEqual(stored_post.shares, 1)
            self.assertEqual(len(stored_shares), 1)
            self.assertTrue(serialized_post.is_shared)

    def test_share_requires_authentication(self) -> None:
        info = SimpleNamespace(context={"user_id": None})
        with self.assertRaises(Exception):
            Mutation().share_post("1", info)


if __name__ == "__main__":
    unittest.main()
