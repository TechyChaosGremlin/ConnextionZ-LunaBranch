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
from backend.app.models import Base, Media, Profile, User


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


if __name__ == "__main__":
    unittest.main()