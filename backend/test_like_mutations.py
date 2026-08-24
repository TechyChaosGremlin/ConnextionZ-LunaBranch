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
from backend.app.models import Base, Notification, Post, PostLike, Profile, User


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


    def test_like_creates_notification_for_post_owner(self) -> None:
        """Liking another user's post should create one unread like notification."""

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "notifications.db"

            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
            )

            Base.metadata.create_all(engine)

            with Session(engine) as session:
                # User who owns the post and should receive the notification.
                owner = User(email="owner@example.test")

                # User who likes the post and becomes the notification actor.
                liker = User(email="liker@example.test")

                session.add_all([owner, liker])
                session.flush()

                owner_profile = Profile(
                    user_id=owner.id,
                    username="post-owner",
                    display_name="Post Owner",
                )

                post = Post(
                    profile=owner_profile,
                    thumbnail="/media/post.jpg",
                    likes=0,
                )

                session.add(post)
                session.commit()

                owner_id = owner.id
                liker_id = liker.id
                post_id = post.id

            # Make like_post() use this test database instead of
            # the application's normal database.
            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(
                context={"user_id": liker_id}
            )

            try:
                with patch(
                    "backend.app.main.get_session",
                    side_effect=get_test_session,
                ):
                    result = Mutation().like_post(
                        str(post_id),
                        info,
                    )

                with Session(engine) as session:
                    notification = session.scalar(
                        select(Notification).where(
                            Notification.recipient_id == owner_id,
                            Notification.actor_id == liker_id,
                            Notification.post_id == post_id,
                        )
                    )

            finally:
                engine.dispose()

            # Existing like behavior should still succeed.
            self.assertTrue(result.liked)

            # A notification should have been created.
            self.assertIsNotNone(notification)

            # Verify the notification contains the correct data.
            self.assertEqual(notification.recipient_id, owner_id)
            self.assertEqual(notification.actor_id, liker_id)
            self.assertEqual(notification.post_id, post_id)
            self.assertEqual(notification.type, "like")
            self.assertEqual(notification.text, "liked your post")
            self.assertFalse(notification.read)

    def test_mark_notification_read(self) -> None:
        """A user should be able to mark their own notification as read."""

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "notifications.db"

            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
            )

            Base.metadata.create_all(engine)

            with Session(engine) as session:
                user = User(email="reader@example.test")
                actor = User(email="actor@example.test")

                session.add_all([user, actor])
                session.flush()

                notification = Notification(
                    recipient_id=user.id,
                    actor_id=actor.id,
                    type="like",
                    text="liked your post",
                    read=False,
                )

                session.add(notification)
                session.commit()

                user_id = user.id
                notification_id = notification.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(
                context={"user_id": user_id}
            )

            try:
                with patch(
                    "backend.app.main.get_session",
                    side_effect=get_test_session,
                ):
                    result = Mutation().mark_notification_read(
                        str(notification_id),
                        info,
                    )

                with Session(engine) as session:
                    saved_notification = session.get(
                        Notification,
                        notification_id,
                    )

            finally:
                engine.dispose()

            self.assertTrue(result)
            self.assertTrue(saved_notification.read)

    def test_mark_all_notifications_read(self) -> None:
        """A user should be able to mark all of their notifications as read."""

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "notifications.db"

            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
            )

            Base.metadata.create_all(engine)

            with Session(engine) as session:
                user = User(email="reader@example.test")
                actor = User(email="actor@example.test")

                session.add_all([user, actor])
                session.flush()

                notification_one = Notification(
                    recipient_id=user.id,
                    actor_id=actor.id,
                    type="like",
                    text="liked your post",
                    read=False,
                )

                notification_two = Notification(
                    recipient_id=user.id,
                    actor_id=actor.id,
                    type="follow",
                    text="started following you",
                    read=False,
                )

                session.add_all([
                    notification_one,
                    notification_two,
                ])
                session.commit()

                user_id = user.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(
                context={"user_id": user_id}
            )

            try:
                with patch(
                    "backend.app.main.get_session",
                    side_effect=get_test_session,
                ):
                    result = Mutation().mark_all_notifications_read(info)

                with Session(engine) as session:
                    saved_notifications = session.scalars(
                        select(Notification).where(
                            Notification.recipient_id == user_id
                        )
                    ).all()

            finally:
                engine.dispose()

            self.assertTrue(result)
            self.assertEqual(len(saved_notifications), 2)
            self.assertTrue(
                all(notification.read for notification in saved_notifications)
            )
    def test_notifications_query_returns_current_users_notifications(self) -> None:
        """The notifications query should only return rows for the logged-in user."""

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "notifications-query.db"

            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
            )

            Base.metadata.create_all(engine)

            with Session(engine) as session:
                recipient = User(email="recipient@example.test")
                actor = User(email="actor@example.test")
                other_user = User(email="other@example.test")

                session.add_all([recipient, actor, other_user])
                session.flush()

                actor_profile = Profile(
                    user_id=actor.id,
                    username="actor-user",
                    display_name="Actor User",
                )

                session.add(actor_profile)
                session.flush()

                notification = Notification(
                    recipient_id=recipient.id,
                    actor_id=actor.id,
                    type="like",
                    text="liked your post",
                    read=False,
                )

                other_notification = Notification(
                    recipient_id=other_user.id,
                    actor_id=actor.id,
                    type="follow",
                    text="started following you",
                    read=False,
                )

                session.add_all([notification, other_notification])
                session.commit()

                recipient_id = recipient.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(
                context={"user_id": recipient_id}
            )

            try:
                with patch(
                    "backend.app.main.get_session",
                    side_effect=get_test_session,
                ):
                    from backend.app.main import Query
                    results = Query().notifications(info)

            finally:
                engine.dispose()

            self.assertEqual(len(results), 1)

            returned = results[0]

            self.assertEqual(returned.type, "like")
            self.assertEqual(returned.actor, "actor-user")
            self.assertEqual(returned.text, "liked your post")
            self.assertFalse(returned.read)


    def test_user_cannot_mark_another_users_notification_read(self) -> None:
        """A user must not be able to update someone else's notification."""

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "notifications-auth.db"

            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
            )

            Base.metadata.create_all(engine)

            with Session(engine) as session:
                owner = User(email="owner@example.test")
                other_user = User(email="other@example.test")
                actor = User(email="actor@example.test")

                session.add_all([owner, other_user, actor])
                session.flush()

                notification = Notification(
                    recipient_id=owner.id,
                    actor_id=actor.id,
                    type="like",
                    text="liked your post",
                    read=False,
                )

                session.add(notification)
                session.commit()

                other_user_id = other_user.id
                notification_id = notification.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(
                context={"user_id": other_user_id}
            )

            try:
                with patch(
                    "backend.app.main.get_session",
                    side_effect=get_test_session,
                ):
                    with self.assertRaises(Exception):
                        Mutation().mark_notification_read(
                            str(notification_id),
                            info,
                        )

                with Session(engine) as session:
                    saved_notification = session.get(
                        Notification,
                        notification_id,
                    )

            finally:
                engine.dispose()

            self.assertFalse(saved_notification.read)


    def test_follow_creates_notification_for_target_user(self) -> None:
        """Following another user should create one unread follow notification."""

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "follow-notification.db"

            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False},
            )

            Base.metadata.create_all(engine)

            with Session(engine) as session:
                follower_user = User(email="follower@example.test")
                target_user = User(email="target@example.test")

                session.add_all([follower_user, target_user])
                session.flush()

                follower_profile = Profile(
                    user_id=follower_user.id,
                    username="follower-user",
                    display_name="Follower User",
                )

                target_profile = Profile(
                    user_id=target_user.id,
                    username="target-user",
                    display_name="Target User",
                )

                session.add_all([follower_profile, target_profile])
                session.commit()

                follower_user_id = follower_user.id
                target_user_id = target_user.id

            def get_test_session() -> Session:
                return Session(engine)

            info = SimpleNamespace(
                context={"user_id": follower_user_id}
            )

            try:
                with patch(
                    "backend.app.main.get_session",
                    side_effect=get_test_session,
                ):
                    result = Mutation().follow(
                        "target-user",
                        info,
                    )

                with Session(engine) as session:
                    notification = session.scalar(
                        select(Notification).where(
                            Notification.recipient_id == target_user_id,
                            Notification.actor_id == follower_user_id,
                            Notification.type == "follow",
                        )
                    )

            finally:
                engine.dispose()

            self.assertTrue(result.following)
            self.assertIsNotNone(notification)
            self.assertEqual(notification.recipient_id, target_user_id)
            self.assertEqual(notification.actor_id, follower_user_id)
            self.assertEqual(notification.type, "follow")
            self.assertEqual(notification.text, "started following you")
            self.assertIsNone(notification.post_id)
            self.assertFalse(notification.read)


if __name__ == "__main__":
    unittest.main()