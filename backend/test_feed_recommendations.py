"""Regression tests for For You feed ranking."""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.main import Query
from backend.app.models import Base, Follow, Post, PostLike, PostReport, Profile, User, UserBlock, UserMute


class FeedRecommendationTests(unittest.TestCase):
    def test_for_you_personalizes_followed_creators_and_interests(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'feed.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                followed_creator = User(email="followed@example.test")
                unrelated_creator = User(email="unrelated@example.test")
                viewer = User(email="viewer@example.test")
                session.add_all([followed_creator, unrelated_creator, viewer])
                session.flush()
                followed_profile = Profile(
                    user_id=followed_creator.id,
                    username="followed",
                    display_name="Followed",
                )
                unrelated_profile = Profile(
                    user_id=unrelated_creator.id,
                    username="unrelated",
                    display_name="Unrelated",
                )
                viewer_profile = Profile(
                    user_id=viewer.id,
                    username="viewer",
                    display_name="Viewer",
                )
                interest_history = Post(
                    profile=unrelated_profile,
                    thumbnail="/history.jpg",
                    hashtags=["jazz"],
                )
                followed_post = Post(
                    profile=followed_profile,
                    thumbnail="/followed.jpg",
                    hashtags=["jazz"],
                )
                unrelated_post = Post(
                    profile=unrelated_profile,
                    thumbnail="/unrelated.jpg",
                    likes=10,
                    hashtags=["rock"],
                )
                session.add_all([viewer_profile, interest_history, followed_post, unrelated_post])
                session.flush()
                session.add_all([
                    Follow(follower_id=viewer.id, following_id=followed_creator.id),
                    PostLike(post_id=interest_history.id, user_id=viewer.id),
                ])
                session.commit()
                followed_id = followed_post.id
                viewer_id = viewer.id

            def get_test_session() -> Session:
                return Session(engine)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    page = Query().feed(SimpleNamespace(context={"user_id": viewer_id}), limit=10, following=False)
            finally:
                engine.dispose()

            self.assertEqual(page.items[0].id, str(followed_id))

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

    def test_for_you_rewards_fresh_engagement_over_stale_reach(self) -> None:
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
                stale_post = Post(
                    profile=profile,
                    thumbnail="/stale.jpg",
                    views=100_000,
                    likes=100,
                    created_at=datetime.utcnow() - timedelta(days=90),
                )
                fresh_post = Post(
                    profile=profile,
                    thumbnail="/fresh.jpg",
                    views=1_000,
                    likes=80,
                    comments=20,
                    shares=10,
                    saves=10,
                    created_at=datetime.utcnow() - timedelta(hours=6),
                )
                session.add_all([stale_post, fresh_post])
                session.commit()
                fresh_id = fresh_post.id
                viewer_id = viewer.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": viewer_id})
            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    page = Query().feed(info, limit=10, following=False)
            finally:
                engine.dispose()

            self.assertEqual(page.items[0].id, str(fresh_id))

    def test_feed_excludes_blocked_muted_reported_and_moderated_posts(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'feed.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                viewer = User(email="viewer@example.test")
                creators = [User(email=f"creator-{index}@example.test") for index in range(7)]
                session.add_all([viewer, *creators])
                session.flush()
                viewer_profile = Profile(user_id=viewer.id, username="viewer", display_name="Viewer")
                profiles = [
                    Profile(user_id=creator.id, username=f"creator-{index}", display_name=f"Creator {index}")
                    for index, creator in enumerate(creators)
                ]
                session.add_all([viewer_profile, *profiles])
                session.flush()
                visible = Post(profile=profiles[0], thumbnail="/visible.jpg", allow_comments=False)
                muted = Post(profile=profiles[1], thumbnail="/muted.jpg")
                blocked = Post(profile=profiles[2], thumbnail="/blocked.jpg")
                blocking_viewer = Post(profile=profiles[3], thumbnail="/blocking.jpg")
                reported = Post(profile=profiles[4], thumbnail="/reported.jpg")
                moderated = Post(profile=profiles[5], thumbnail="/moderated.jpg", moderation_status="under_review")
                deleted = Post(profile=profiles[6], thumbnail="/deleted.jpg", status="deleted")
                session.add_all([visible, muted, blocked, blocking_viewer, reported, moderated, deleted])
                session.flush()
                session.add_all([
                    UserMute(muter_id=viewer.id, muted_id=creators[1].id),
                    UserBlock(blocker_id=viewer.id, blocked_id=creators[2].id),
                    UserBlock(blocker_id=creators[3].id, blocked_id=viewer.id),
                    PostReport(post_id=reported.id, reporter_id=viewer.id),
                ])
                session.commit()
                viewer_id = viewer.id
                visible_id = visible.id

            def get_test_session() -> Session:
                return Session(engine)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    page = Query().feed(SimpleNamespace(context={"user_id": viewer_id}), limit=10)
                    comments = Query().comments(str(visible_id), SimpleNamespace(context={"user_id": viewer_id}))
            finally:
                engine.dispose()

            self.assertEqual([item.id for item in page.items], [str(visible_id)])
            self.assertFalse(page.items[0].allow_comments)
            self.assertEqual(comments, [])

    def test_disabled_collaboration_does_not_receive_collaboration_boost(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'feed.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                viewer = User(email="viewer@example.test")
                creator = User(email="creator@example.test")
                session.add_all([viewer, creator])
                session.flush()
                viewer_profile = Profile(
                    user_id=viewer.id,
                    username="viewer",
                    display_name="Viewer",
                    open_to_collab=True,
                )
                creator_profile = Profile(
                    user_id=creator.id,
                    username="creator",
                    display_name="Creator",
                    open_to_collab=True,
                )
                eligible = Post(
                    profile=creator_profile,
                    thumbnail="/eligible.jpg",
                    collab_with="viewer",
                    allow_collabs=True,
                )
                disabled = Post(
                    profile=creator_profile,
                    thumbnail="/disabled.jpg",
                    collab_with="viewer",
                    allow_collabs=False,
                )
                session.add_all([viewer_profile, creator_profile, eligible, disabled])
                session.commit()
                viewer_id = viewer.id
                eligible_id = eligible.id

            def get_test_session() -> Session:
                return Session(engine)

            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    page = Query().feed(SimpleNamespace(context={"user_id": viewer_id}), limit=10)
            finally:
                engine.dispose()

            self.assertEqual(page.items[0].id, str(eligible_id))

    def test_feed_cursor_does_not_repeat_items_after_new_top_post(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'feed.db'}")
            Base.metadata.create_all(engine)
            with Session(engine) as session:
                creator = User(email="creator@example.test")
                session.add(creator)
                session.flush()
                profile = Profile(user_id=creator.id, username="creator", display_name="Creator")
                session.add_all([
                    Post(profile=profile, thumbnail="/top.jpg", likes=30),
                    Post(profile=profile, thumbnail="/middle.jpg", likes=20),
                    Post(profile=profile, thumbnail="/bottom.jpg", likes=10),
                ])
                session.commit()

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(context={"user_id": None})
            try:
                with patch("backend.app.main.get_session", side_effect=get_test_session):
                    first_page = Query().feed(info, limit=2)
                    with Session(engine) as session:
                        profile = session.scalar(select(Profile).where(Profile.username == "creator"))
                        session.add(Post(profile=profile, thumbnail="/new-top.jpg", likes=50))
                        session.commit()
                    second_page = Query().feed(info, cursor=first_page.next_cursor, limit=2)
            finally:
                engine.dispose()

            first_page_ids = {item.id for item in first_page.items}
            self.assertEqual(len(first_page_ids & {item.id for item in second_page.items}), 0)
            self.assertEqual([item.thumbnail for item in second_page.items], ["/bottom.jpg"])


if __name__ == "__main__":
    unittest.main()