"""Regression tests for profile identifier resolution."""

import asyncio
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from graphql import GraphQLError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.main import AVATAR_TYPES, MAX_AVATAR_BYTES, Mutation, PostInput, find_profile, parse_int_id, store_upload
from backend.app.main import Query
from backend.app.graphql_types import UpdateProfileInput
from backend.app.models import Base, Follow, Media, Post, Profile, User


class FindProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        self.session.add_all([
            User(id=123, email="id-owner@example.test"),
            User(id=456, email="numeric-owner@example.test"),
            Profile(
                id=123,
                user_id=123,
                username="id-owner",
                display_name="ID Owner",
            ),
            Profile(
                id=456,
                user_id=456,
                username="123",
                display_name="Numeric Username Owner",
            ),
        ])
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()

    def test_numeric_username_takes_precedence_over_profile_id(self) -> None:
        profile = find_profile(self.session, "123")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.id, 456)
        self.assertEqual(profile.username, "123")

    def test_parse_int_id_rejects_non_numeric_values(self) -> None:
        with self.assertRaises(GraphQLError):
            parse_int_id("abc", "Post ID")

    def test_avatar_upload_rejects_files_larger_than_8mb(self) -> None:
        async def upload_too_large() -> None:
            upload = UploadFile(
                filename="avatar.jpg",
                file=io.BytesIO(b"x" * (MAX_AVATAR_BYTES + 1)),
                headers={"content-type": "image/jpeg"},
            )
            with self.assertRaises(HTTPException) as error:
                await store_upload(upload, AVATAR_TYPES, MAX_AVATAR_BYTES)
            self.assertEqual(error.exception.status_code, 413)

        asyncio.run(upload_too_large())

    def test_avatar_upload_rejects_spoofed_content_type(self) -> None:
        async def upload_spoofed_file() -> None:
            upload = UploadFile(
                filename="avatar.png",
                file=io.BytesIO(b"<script>alert('not an image')</script>"),
                headers={"content-type": "image/png"},
            )
            with self.assertRaises(HTTPException) as error:
                await store_upload(upload, AVATAR_TYPES, MAX_AVATAR_BYTES)
            self.assertEqual(error.exception.status_code, 415)

        asyncio.run(upload_spoofed_file())

    def test_create_post_requires_media_owned_by_the_authenticated_user(self) -> None:
        owned_media = Media(user_id=123, url="/media/owned.mp4", content_type="video/mp4")
        owned_thumbnail = Media(user_id=123, url="/media/owned.jpg", content_type="image/jpeg")
        other_media = Media(user_id=456, url="/media/other.mp4", content_type="video/mp4")
        self.session.add_all([owned_media, owned_thumbnail, other_media])
        self.session.commit()
        owned_media_id = str(owned_media.id)
        owned_thumbnail_id = str(owned_thumbnail.id)
        other_media_id = str(other_media.id)
        owned_media_url = owned_media.url
        owned_thumbnail_url = owned_thumbnail.url
        info = SimpleNamespace(context={"user_id": 123})

        with patch("backend.app.main.get_session", return_value=self.session):
            post = Mutation().create_post(PostInput(
                media_id=owned_media_id,
                thumbnail_media_id=owned_thumbnail_id,
            ), info)
        self.assertEqual(post.media_url, owned_media_url)
        self.assertEqual(post.thumbnail, owned_thumbnail_url)

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as error:
                Mutation().create_post(PostInput(
                    media_id=other_media_id,
                    thumbnail_media_id=owned_thumbnail_id,
                ), info)
        self.assertEqual(error.exception.extensions["code"], "NOT_FOUND")

    def test_create_post_can_save_draft_status(self) -> None:
        owned_media = Media(user_id=123, url="/media/owned.mp4", content_type="video/mp4")
        owned_thumbnail = Media(user_id=123, url="/media/owned.jpg", content_type="image/jpeg")
        self.session.add_all([owned_media, owned_thumbnail])
        self.session.commit()
        info = SimpleNamespace(context={"user_id": 123})

        with patch("backend.app.main.get_session", return_value=self.session):
            post = Mutation().create_post(PostInput(
                media_id=str(owned_media.id),
                thumbnail_media_id=str(owned_thumbnail.id),
                status="draft",
            ), info)

        self.assertEqual(post.status, "draft")

    def test_create_post_rejects_unknown_status(self) -> None:
        owned_media = Media(user_id=123, url="/media/owned.mp4", content_type="video/mp4")
        owned_thumbnail = Media(user_id=123, url="/media/owned.jpg", content_type="image/jpeg")
        self.session.add_all([owned_media, owned_thumbnail])
        self.session.commit()
        info = SimpleNamespace(context={"user_id": 123})

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as error:
                Mutation().create_post(PostInput(
                    media_id=str(owned_media.id),
                    thumbnail_media_id=str(owned_thumbnail.id),
                    status="archived",
                ), info)
        self.assertEqual(error.exception.extensions["code"], "VALIDATION_ERROR")


class ProfileQueryMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)

        # Target account and followers used by pagination tests.
        self.target = User(email="target@example.test")
        self.viewer = User(email="viewer@example.test")
        self.follower_one = User(email="follower1@example.test")
        self.follower_two = User(email="follower2@example.test")
        self.follower_three = User(email="follower3@example.test")

        # Accounts used by suggested profile ordering and username conflict checks.
        self.editor = User(email="editor@example.test")
        self.other_editor = User(email="other-editor@example.test")
        self.session.add_all([
            self.target,
            self.viewer,
            self.follower_one,
            self.follower_two,
            self.follower_three,
            self.editor,
            self.other_editor,
        ])
        self.session.flush()

        self.target_profile = Profile(
            user_id=self.target.id,
            username="target",
            display_name="Target",
        )
        self.viewer_profile = Profile(
            user_id=self.viewer.id,
            username="viewer",
            display_name="Viewer",
        )
        self.follower_profile_one = Profile(
            user_id=self.follower_one.id,
            username="follower.one",
            display_name="Follower One",
            collab_score=4.4,
            followers=100,
            open_to_collab=True,
        )
        self.follower_profile_two = Profile(
            user_id=self.follower_two.id,
            username="follower.two",
            display_name="Follower Two",
            collab_score=4.4,
            followers=60,
            open_to_collab=True,
        )
        self.follower_profile_three = Profile(
            user_id=self.follower_three.id,
            username="follower.three",
            display_name="Follower Three",
            collab_score=4.9,
            followers=20,
            open_to_collab=True,
        )
        self.editor_profile = Profile(
            user_id=self.editor.id,
            username="edit.me",
            display_name="Edit Me",
            collab_score=4.6,
            followers=250,
            open_to_collab=True,
            bio="before",
            location="old-town",
            website="https://old.example.test",
        )
        self.other_editor_profile = Profile(
            user_id=self.other_editor.id,
            username="taken.name",
            display_name="Taken Name",
            collab_score=5.0,
            followers=1,
            open_to_collab=False,
        )
        self.private_owner = User(email="private-owner@example.test")
        self.private_follower = User(email="private-follower@example.test")
        self.session.add_all([self.private_owner, self.private_follower])
        self.session.flush()

        self.private_owner_profile = Profile(
            user_id=self.private_owner.id,
            username="private.owner",
            display_name="Private Owner",
            private_account=True,
        )
        self.private_follower_profile = Profile(
            user_id=self.private_follower.id,
            username="private.follower",
            display_name="Private Follower",
        )

        self.session.add_all([
            self.target_profile,
            self.viewer_profile,
            self.follower_profile_one,
            self.follower_profile_two,
            self.follower_profile_three,
            self.editor_profile,
            self.other_editor_profile,
            self.private_owner_profile,
            self.private_follower_profile,
        ])
        self.session.flush()

        self.session.add_all([
            Follow(follower_id=self.follower_one.id, following_id=self.target.id),
            Follow(follower_id=self.follower_two.id, following_id=self.target.id),
            Follow(follower_id=self.follower_three.id, following_id=self.target.id),
            # Viewer follows follower_two so isFollowing can be asserted per row.
            Follow(follower_id=self.viewer.id, following_id=self.follower_two.id),
            Follow(follower_id=self.private_follower.id, following_id=self.private_owner.id),
        ])
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()

    def test_suggested_profiles_rank_and_filter_open_to_collab(self) -> None:
        info = SimpleNamespace(context={"user_id": None})
        with patch("backend.app.main.get_session", return_value=self.session):
            rows = Query().suggested_profiles(info, limit=4)

        usernames = [row.username for row in rows]
        # Ranked by score descending, then followers descending.
        self.assertEqual(
            usernames[:4],
            ["follower.three", "edit.me", "follower.one", "follower.two"],
        )
        self.assertNotIn("taken.name", usernames)

    def test_followers_page_paginates_and_sets_is_following(self) -> None:
        info = SimpleNamespace(context={"user_id": self.viewer.id})
        with patch("backend.app.main.get_session", return_value=self.session):
            first_page = Query().followers_page("target", info, limit=2)
            second_page = Query().followers_page("target", info, after=first_page.next_cursor, limit=2)

        self.assertEqual([profile.username for profile in first_page.profiles], ["follower.one", "follower.two"])
        self.assertEqual(first_page.next_cursor, "2")
        self.assertEqual([profile.is_following for profile in first_page.profiles], [False, True])
        self.assertEqual([profile.username for profile in second_page.profiles], ["follower.three"])
        self.assertIsNone(second_page.next_cursor)

    def test_profile_query_accepts_numeric_profile_id(self) -> None:
        info = SimpleNamespace(context={"user_id": None})
        with patch("backend.app.main.get_session", return_value=self.session):
            profile = Query().profile(str(self.target_profile.id), info)

        self.assertIsNotNone(profile)
        self.assertEqual(profile.username, "target")
        self.assertEqual(profile.display_name, "Target")

    def test_private_profile_hidden_from_non_follower(self) -> None:
        anonymous = SimpleNamespace(context={"user_id": None})
        follower = SimpleNamespace(context={"user_id": self.private_follower.id})

        with patch("backend.app.main.get_session", return_value=self.session):
            hidden = Query().profile("private.owner", anonymous)
            visible = Query().profile("private.owner", follower)

        self.assertIsNone(hidden)
        self.assertIsNotNone(visible)
        self.assertEqual(visible.username, "private.owner")

    def test_profile_query_hides_drafts_from_other_viewers(self) -> None:
        published = Post(profile=self.target_profile, thumbnail="/media/published.jpg", status="published")
        draft = Post(profile=self.target_profile, thumbnail="/media/draft.jpg", status="draft")
        self.session.add_all([published, draft])
        self.session.commit()

        anonymous = SimpleNamespace(context={"user_id": None})
        owner = SimpleNamespace(context={"user_id": self.target.id})

        with patch("backend.app.main.get_session", return_value=self.session):
            public_profile = Query().profile("target", anonymous)
            owner_profile = Query().profile("target", owner)

        self.assertEqual([post.status for post in public_profile.posts], ["published"])
        self.assertEqual([post.status for post in owner_profile.posts], ["published", "draft"])

    def test_feed_and_search_hide_drafts(self) -> None:
        self.session.add_all([
            Post(profile=self.target_profile, thumbnail="/media/published.jpg", caption="launch song", status="published"),
            Post(profile=self.target_profile, thumbnail="/media/draft.jpg", caption="launch draft", status="draft"),
        ])
        self.session.commit()
        info = SimpleNamespace(context={"user_id": None})

        with patch("backend.app.main.get_session", return_value=self.session):
            feed = Query().feed(info)
            search = Query().search_posts(info, "launch")

        self.assertEqual([post.status for post in feed.items], ["published"])
        self.assertEqual([post.status for post in search], ["published"])

    def test_following_feed_only_includes_followed_creators(self) -> None:
        followed_post = Post(
            profile=self.target_profile,
            thumbnail="/media/followed.jpg",
            caption="followed post",
            status="published",
        )
        unfollowed_post = Post(
            profile=self.editor_profile,
            thumbnail="/media/unfollowed.jpg",
            caption="unfollowed post",
            status="published",
        )
        self.session.add_all([followed_post, unfollowed_post])
        self.session.flush()
        self.session.add(Follow(follower_id=self.viewer.id, following_id=self.target.id))
        self.session.commit()
        info = SimpleNamespace(context={"user_id": self.viewer.id})

        with patch("backend.app.main.get_session", return_value=self.session):
            feed = Query().feed(info, following=True)

        self.assertEqual([post.caption for post in feed.items], ["followed post"])

    def test_anonymous_following_feed_is_empty(self) -> None:
        info = SimpleNamespace(context={"user_id": None})

        with patch("backend.app.main.get_session", return_value=self.session):
            feed = Query().feed(info, following=True)

        self.assertEqual(feed.items, [])
        self.assertIsNone(feed.next_cursor)

    def test_update_profile_normalizes_username_and_persists_fields(self) -> None:
        info = SimpleNamespace(context={"user_id": self.editor.id})
        with patch("backend.app.main.get_session", return_value=self.session):
            updated = Mutation().update_profile(UpdateProfileInput(
                username="@Editor.New",
                display_name="  Editor    Updated  ",
                bio="  updated bio  ",
                location="new-town",
                website="example.com",
                avatar_url="  https://cdn.example.com/avatar.png  ",
            ), info)

        self.assertEqual(updated.username, "editor.new")
        self.assertEqual(updated.display_name, "Editor Updated")
        self.assertEqual(updated.bio, "updated bio")
        self.assertEqual(updated.location, "new-town")
        self.assertEqual(updated.website, "https://example.com")
        self.assertEqual(updated.avatar_url, "https://cdn.example.com/avatar.png")

        reloaded = self.session.get(Profile, self.editor_profile.id)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.username, "editor.new")
        self.assertEqual(reloaded.display_name, "Editor Updated")
        self.assertEqual(reloaded.website, "https://example.com")
        self.assertEqual(reloaded.avatar_url, "https://cdn.example.com/avatar.png")

    def test_update_profile_rejects_invalid_or_taken_username(self) -> None:
        info = SimpleNamespace(context={"user_id": self.editor.id})

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as invalid_error:
                Mutation().update_profile(UpdateProfileInput(username="bad name with spaces"), info)
        self.assertEqual(invalid_error.exception.extensions["code"], "VALIDATION_ERROR")

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as conflict_error:
                Mutation().update_profile(UpdateProfileInput(username="taken.name"), info)
        self.assertEqual(conflict_error.exception.extensions["code"], "CONFLICT")

    def test_update_profile_rejects_invalid_display_name_bio_website_and_avatar_url(self) -> None:
        info = SimpleNamespace(context={"user_id": self.editor.id})

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as display_name_error:
                Mutation().update_profile(UpdateProfileInput(display_name="   "), info)
        self.assertEqual(display_name_error.exception.extensions["code"], "VALIDATION_ERROR")

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as bio_error:
                Mutation().update_profile(UpdateProfileInput(bio=("x" * 161)), info)
        self.assertEqual(bio_error.exception.extensions["code"], "VALIDATION_ERROR")

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as website_error:
                Mutation().update_profile(UpdateProfileInput(website="not-a-url"), info)
        self.assertEqual(website_error.exception.extensions["code"], "VALIDATION_ERROR")

        with patch("backend.app.main.get_session", return_value=self.session):
            with self.assertRaises(GraphQLError) as avatar_error:
                Mutation().update_profile(UpdateProfileInput(avatar_url="javascript:alert(1)"), info)
        self.assertEqual(avatar_error.exception.extensions["code"], "VALIDATION_ERROR")

    def test_update_profile_can_toggle_private_account(self) -> None:
        info = SimpleNamespace(context={"user_id": self.editor.id})
        with patch("backend.app.main.get_session", return_value=self.session):
            updated = Mutation().update_profile(UpdateProfileInput(private_account=True), info)

        self.assertTrue(updated.private_account)

        reloaded = self.session.get(Profile, self.editor_profile.id)
        self.assertIsNotNone(reloaded)
        self.assertTrue(reloaded.private_account)


if __name__ == "__main__":
    unittest.main()
