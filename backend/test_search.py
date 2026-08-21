"""Regression tests for search: visibility rules, ranking, pagination, history."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.main import Mutation, Query
from backend.app.models import Base, Follow, Post, Profile, SearchQuery, User, UserBlock


def info_for(user_id: int | None) -> SimpleNamespace:
    return SimpleNamespace(context={"user_id": user_id})


class SearchVisibilityTests(unittest.TestCase):
    """searchProfiles / searchPosts / searchHashtags must never leak content the
    equivalent feed/profile queries would hide."""

    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)

        self.session.add_all([
            User(id=1, email="public@example.test"),
            User(id=2, email="private@example.test"),
            User(id=3, email="viewer@example.test"),
            Profile(id=1, user_id=1, username="publicdj", display_name="Public DJ", followers=10),
            Profile(id=2, user_id=2, username="privatedj", display_name="Private DJ", private_account=True),
            Profile(id=3, user_id=3, username="viewer", display_name="Viewer"),
        ])
        self.session.commit()
        self.get_session_patch = patch("backend.app.main.get_session", return_value=self.session)
        self.get_session_patch.start()

    def tearDown(self) -> None:
        self.get_session_patch.stop()
        self.session.close()

    def test_search_profiles_hides_private_accounts_from_strangers(self) -> None:
        page = Query().search_profiles(query="dj", info=info_for(None))
        usernames = {p.username for p in page.profiles}
        self.assertIn("publicdj", usernames)
        self.assertNotIn("privatedj", usernames)

    def test_search_profiles_shows_private_account_to_followers(self) -> None:
        self.session.add(Follow(follower_id=3, following_id=2))
        self.session.commit()
        page = Query().search_profiles(query="dj", info=info_for(3))
        usernames = {p.username for p in page.profiles}
        self.assertIn("privatedj", usernames)

    def test_search_posts_hides_draft_and_pending_moderation_posts(self) -> None:
        self.session.add_all([
            Post(id=1, profile_id=1, thumbnail="t.jpg", caption="berlin techno set", status="published", moderation_status="approved", views=5),
            Post(id=2, profile_id=1, thumbnail="t.jpg", caption="berlin draft", status="draft", moderation_status="approved", views=999),
            Post(id=3, profile_id=1, thumbnail="t.jpg", caption="berlin flagged", status="published", moderation_status="pending", views=999),
        ])
        self.session.commit()
        page = Query().search_posts(info=info_for(None), query="berlin")
        ids = {item.id for item in page.items}
        self.assertEqual(ids, {"1"})

    def test_search_posts_respects_followers_only_visibility(self) -> None:
        self.session.add(Post(
            id=1, profile_id=1, thumbnail="t.jpg", caption="berlin techno set",
            status="published", moderation_status="approved", visibility="followers", views=5,
        ))
        self.session.commit()
        anon_page = Query().search_posts(info=info_for(None), query="berlin")
        self.assertEqual(anon_page.items, [])

        follower_page = Query().search_posts(info=info_for(3), query="berlin")
        self.assertEqual(follower_page.items, [])  # not following yet

        self.session.add(Follow(follower_id=3, following_id=1))
        self.session.commit()
        follower_page = Query().search_posts(info=info_for(3), query="berlin")
        self.assertEqual(len(follower_page.items), 1)

    def test_search_posts_hides_posts_from_blocked_relationship(self) -> None:
        self.session.add_all([
            Post(id=1, profile_id=1, thumbnail="t.jpg", caption="berlin techno set", status="published", moderation_status="approved", views=5),
            UserBlock(blocker_id=1, blocked_id=3),
        ])
        self.session.commit()
        page = Query().search_posts(info=info_for(3), query="berlin")
        self.assertEqual(page.items, [])

    def test_search_hashtags_ignores_unapproved_posts(self) -> None:
        self.session.add_all([
            Post(id=1, profile_id=1, thumbnail="t.jpg", hashtags=["techno"], status="published", moderation_status="approved", views=5),
            Post(id=2, profile_id=1, thumbnail="t.jpg", hashtags=["technoflagged"], status="published", moderation_status="pending", views=999),
        ])
        self.session.commit()
        page = Query().search_hashtags(query="techno")
        tags = {h.tag for h in page.hashtags}
        self.assertEqual(tags, {"techno"})


class SearchRankingTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        self.session.add_all([
            User(id=1, email="exact@example.test"),
            User(id=2, email="bio@example.test"),
            # Fewer followers, but an exact handle match should still rank first.
            Profile(id=1, user_id=1, username="nova", display_name="Nova", followers=5),
            Profile(id=2, user_id=2, username="novafan99", display_name="Big Nova Fan", followers=500),
        ])
        self.session.commit()
        self.get_session_patch = patch("backend.app.main.get_session", return_value=self.session)
        self.get_session_patch.start()

    def tearDown(self) -> None:
        self.get_session_patch.stop()
        self.session.close()

    def test_exact_handle_match_outranks_more_popular_substring_match(self) -> None:
        page = Query().search_profiles(query="nova", info=info_for(None))
        usernames = [p.username for p in page.profiles]
        self.assertEqual(usernames[0], "nova")


class SearchPaginationTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        self.session.add(User(id=1, email="creator@example.test"))
        self.session.add(Profile(id=1, user_id=1, username="creator", display_name="Creator"))
        self.session.add_all([
            Post(id=i, profile_id=1, thumbnail="t.jpg", caption="berlin set", status="published", moderation_status="approved", views=i)
            for i in range(1, 6)
        ])
        self.session.commit()
        self.get_session_patch = patch("backend.app.main.get_session", return_value=self.session)
        self.get_session_patch.start()

    def tearDown(self) -> None:
        self.get_session_patch.stop()
        self.session.close()

    def test_search_posts_paginates_with_next_cursor(self) -> None:
        first = Query().search_posts(info=info_for(None), query="berlin", limit=2)
        self.assertEqual(len(first.items), 2)
        self.assertIsNotNone(first.next_cursor)

        second = Query().search_posts(info=info_for(None), query="berlin", after=first.next_cursor, limit=2)
        self.assertEqual(len(second.items), 2)
        self.assertNotEqual({i.id for i in first.items}, {i.id for i in second.items})

        third = Query().search_posts(info=info_for(None), query="berlin", after=second.next_cursor, limit=2)
        self.assertEqual(len(third.items), 1)
        self.assertIsNone(third.next_cursor)


class SearchHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        self.session.add(User(id=1, email="viewer@example.test"))
        self.session.commit()
        self.get_session_patch = patch("backend.app.main.get_session", return_value=self.session)
        self.get_session_patch.start()

    def tearDown(self) -> None:
        self.get_session_patch.stop()
        self.session.close()

    def test_search_history_requires_auth_and_dedupes(self) -> None:
        self.assertEqual(Query().search_history(info=info_for(None)), [])

        self.assertTrue(Mutation().record_search(query="Berlin DJ", info=info_for(1)))
        self.assertTrue(Mutation().record_search(query="berlin dj", info=info_for(1)))
        self.assertTrue(Mutation().record_search(query="techno", info=info_for(1)))

        history = Query().search_history(info=info_for(1))
        queries = [h.query for h in history]
        self.assertEqual(queries, ["techno", "berlin dj"])

    def test_clear_search_history_removes_only_the_caller_entries(self) -> None:
        self.session.add(User(id=2, email="other@example.test"))
        self.session.commit()
        Mutation().record_search(query="alpha", info=info_for(1))
        Mutation().record_search(query="beta", info=info_for(2))

        self.assertTrue(Mutation().clear_search_history(info=info_for(1)))

        self.assertEqual(Query().search_history(info=info_for(1)), [])
        self.assertEqual(len(Query().search_history(info=info_for(2))), 1)

    def test_search_suggestions_include_creator_and_history_matches(self) -> None:
        self.session.add(Profile(id=1, user_id=1, username="berlinbeats", display_name="Berlin Beats"))
        self.session.commit()
        Mutation().record_search(query="berlin nights", info=info_for(1))

        suggestions = Query().search_suggestions(prefix="berlin", info=info_for(1))
        types = {s.type for s in suggestions}
        self.assertIn("creator", types)
        self.assertIn("query", types)


if __name__ == "__main__":
    unittest.main()
