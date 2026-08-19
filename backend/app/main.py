from __future__ import annotations

import os
import re
import logging
import time
from typing import Optional

import strawberry
from graphql import GraphQLError
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from backend.app.auth import get_user_profile, AuthContext
from backend.app.auth_routes import create_auth_router
from backend.app.database import get_session
from backend.app.models import Follow, Media as DbMedia, Playlist as DbPlaylist, Post as DbPost, Profile as DbProfile, Sound as DbSound, User
from backend.app.media import AVATAR_TYPES, MAX_AVATAR_BYTES, MAX_MEDIA_BYTES, MEDIA_ROOT, MEDIA_TYPES, store_upload
from backend.app.media_routes import create_media_router
from backend.app.graphql_types import (
    ContentItem, FeedItem, FeedPage, FollowResult, HashtagResult, Playlist,
    PlaylistInput, PostInput, Profile, ProfilePage, ProfileSummary, SoundResult,
    UpdatePlaylistInput, UpdatePostInput, UpdateProfileInput,
)
from backend.app.seed import seed_database
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("connextionz.api")


def api_error(message: str, code: str, status_code: int) -> GraphQLError:
    return GraphQLError(message, extensions={"code": code, "statusCode": status_code})


def parse_int_id(raw_id: object, field_name: str = "ID") -> int:
    if raw_id is None:
        raise api_error(f"{field_name} is required", "VALIDATION_ERROR", 400)

    value = str(raw_id).strip()
    if not value or not re.fullmatch(r"\d+", value):
        raise api_error(f"Invalid {field_name}: expected a numeric ID", "VALIDATION_ERROR", 400)

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise api_error(f"Invalid {field_name}: expected a numeric ID", "VALIDATION_ERROR", 400) from exc


seed_database()


def sound_to_graphql(sound: DbSound) -> SoundResult:
    return SoundResult(
        id=sound.id, title=sound.title, creator=sound.creator,
        creator_avatar=sound.creator_avatar, artwork=sound.artwork,
        genre=sound.genre, video_count=sound.video_count,
        total_plays=sound.total_plays, rank=sound.rank,
        growth_pct=sound.growth_pct, duration=sound.duration, bpm=sound.bpm,
    )


def post_to_graphql(post: DbPost) -> ContentItem:
    return ContentItem(
        id=str(post.id), thumbnail=post.thumbnail, media_url=post.media_url,
        caption=post.caption or "", views=post.views, likes=post.likes,
        collab_with=post.collab_with, hashtags=post.hashtags or [],
        audio=post.audio or "Original Sound", visibility=post.visibility or "public",
        allow_comments=post.allow_comments if post.allow_comments is not None else True,
        allow_collabs=post.allow_collabs if post.allow_collabs is not None else True,
        duration_sec=post.duration_sec or 0.0, comments=post.comments or 0,
        shares=post.shares or 0, saves=post.saves or 0,
    )


def profile_to_graphql(profile: DbProfile, is_following: bool = False) -> Profile:
    posts = [post_to_graphql(post) for post in profile.posts]
    playlists = [
        Playlist(
            id=str(item.id),
            title=item.title,
            cover=item.cover,
            item_label=item.item_label,
            plays=item.plays,
        )
        for item in profile.playlists
    ]

    return Profile(
        id=str(profile.id),
        username=profile.username,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url or "",
        avatar_color=profile.avatar_color or "#00AEEF",
        bio=profile.bio,
        location=profile.location,
        website=profile.website,
        verified=profile.verified,
        online=profile.online,
        collab_status=profile.collab_status,
        collab_score=profile.collab_score,
        collab_count=profile.collab_count,
        followers=profile.followers,
        following=profile.following,
        open_to_collab=profile.open_to_collab,
        response_time=profile.response_time,
        posts=posts,
        playlists=playlists,
        is_following=is_following,
    )


def load_profile_from_db(username: str | None = None) -> DbProfile | None:
    with get_session() as session:
        stmt = select(DbProfile)
        if username is not None:
            stmt = stmt.where(DbProfile.username == username)
        profile = session.execute(stmt).scalars().first()
        if profile is None:
            return None

        return profile


def owner_profile(session, info: Info) -> DbProfile:
    user_id = info.context.get("user_id")
    if user_id is None:
        raise api_error("Must be logged in", "UNAUTHENTICATED", 401)
    profile = session.execute(
        select(DbProfile).where(DbProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None:
        raise api_error("Profile not found", "NOT_FOUND", 404)
    return profile


def owned_media(session, user_id: int, media_id: object, field_name: str) -> DbMedia:
    record_id = parse_int_id(media_id, field_name)
    media = session.execute(
        select(DbMedia).where(DbMedia.id == record_id, DbMedia.user_id == user_id)
    ).scalar_one_or_none()
    if media is None:
        raise api_error("Media not found", "NOT_FOUND", 404)
    return media


def profile_summary(profile: DbProfile, is_following: bool = False) -> ProfileSummary:
    return ProfileSummary(
        id=str(profile.id), username=profile.username,
        display_name=profile.display_name, avatar_url=profile.avatar_url or "",
        avatar_color=profile.avatar_color or "#00AEEF", verified=profile.verified,
        collab_score=profile.collab_score, collab_count=profile.collab_count,
        followers=profile.followers, following=profile.following,
        open_to_collab=profile.open_to_collab, is_following=is_following,
    )


def find_profile(session, identifier: str) -> DbProfile | None:
    identifier = identifier.strip()
    profile = session.execute(
        select(DbProfile).where(DbProfile.username == identifier)
    ).scalar_one_or_none()
    if profile is not None or not identifier.isdigit():
        return profile
    try:
        numeric_id = int(identifier)
    except (TypeError, ValueError):
        return profile
    return session.execute(
        select(DbProfile).where(DbProfile.id == numeric_id)
    ).scalar_one_or_none()


def feed_item(post: DbPost, profile: DbProfile) -> FeedItem:
    return FeedItem(
        id=str(post.id), thumbnail=post.thumbnail, media_url=post.media_url,
        caption=post.caption or "", views=post.views, likes=post.likes,
        collab_with=post.collab_with, hashtags=post.hashtags or [],
        audio=post.audio or "Original Sound", visibility=post.visibility or "public",
        allow_comments=post.allow_comments if post.allow_comments is not None else True,
        allow_collabs=post.allow_collabs if post.allow_collabs is not None else True,
        duration_sec=post.duration_sec or 0.0, comments=post.comments or 0,
        shares=post.shares or 0, saves=post.saves or 0,
        creator=profile_summary(profile),
    )


@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: Info) -> Profile | None:
        """Return the logged-in user's profile, or None if not authenticated."""
        user_id = info.context.get("user_id")
        if user_id is None:
            return None

        profile = get_user_profile(user_id)
        if profile is None:
            return None
        return profile_to_graphql(profile)

    @strawberry.field
    def profile(self, username: str, info: Info) -> Profile | None:
        """Fetch any user's public profile by username."""
        with get_session() as session:
            profile = session.execute(
                select(DbProfile).where(DbProfile.username == username)
            ).scalar_one_or_none()
            if profile is None:
                return None
            user_id = info.context.get("user_id")
            is_following = False
            if user_id is not None and user_id != profile.user_id:
                is_following = session.execute(
                    select(Follow.id).where(
                        Follow.follower_id == user_id,
                        Follow.following_id == profile.user_id,
                    )
                ).first() is not None
            return profile_to_graphql(profile, is_following=is_following)

    @strawberry.field(name="searchProfiles")
    def search_profiles(self, query: str, limit: int = 20) -> list[ProfileSummary]:
        """Search public profiles by username or display name."""
        terms = [term for term in query.strip().split() if term]
        if not terms:
            return []
        search = "%" + "%".join(terms) + "%"
        page_size = max(1, min(limit, 50))
        with get_session() as session:
            profiles = session.execute(
                select(DbProfile)
                .where(or_(
                    func.lower(DbProfile.username).like(search.lower()),
                    func.lower(DbProfile.display_name).like(search.lower()),
                ))
                .order_by(DbProfile.followers.desc(), DbProfile.username)
                .limit(page_size)
            ).scalars().all()
            return [profile_summary(profile) for profile in profiles]

    @strawberry.field(name="suggestedProfiles")
    def suggested_profiles(self, limit: int = 6) -> list[ProfileSummary]:
        """Return public profiles ranked for collaboration discovery."""
        page_size = max(1, min(limit, 20))
        with get_session() as session:
            profiles = session.execute(
                select(DbProfile)
                .where(DbProfile.open_to_collab.is_(True))
                .order_by(DbProfile.collab_score.desc(), DbProfile.followers.desc())
                .limit(page_size)
            ).scalars().all()
            return [profile_summary(profile) for profile in profiles]

    @strawberry.field(name="searchPosts")
    def search_posts(self, query: str, limit: int = 20) -> list[FeedItem]:
        """Search published posts by caption, hashtag, audio, or creator."""
        terms = [term for term in query.strip().split() if term]
        if not terms:
            return []
        page_size = max(1, min(limit, 50))
        with get_session() as session:
            filters = []
            for term in terms:
                pattern = f"%{term}%"
                filters.append(or_(
                    DbPost.caption.ilike(pattern),
                    DbPost.audio.ilike(pattern),
                    cast(DbPost.hashtags, String).ilike(pattern),
                    DbProfile.username.ilike(pattern),
                    DbProfile.display_name.ilike(pattern),
                ))
            rows = session.execute(
                select(DbPost, DbProfile)
                .join(DbProfile, DbPost.profile_id == DbProfile.id)
                .where(*filters)
                .order_by(DbPost.views.desc(), DbPost.id.desc())
                .limit(page_size)
            ).all()
            return [feed_item(post, profile) for post, profile in rows]

    @strawberry.field(name="searchHashtags")
    def search_hashtags(self, query: str, limit: int = 20) -> list[HashtagResult]:
        """Search hashtags stored on published posts."""
        term = query.strip().lstrip("#").lower()
        if not term:
            return []
        page_size = max(1, min(limit, 50))
        counts: dict[str, tuple[int, int]] = {}
        with get_session() as session:
            posts = session.execute(select(DbPost.hashtags, DbPost.views)).all()
        for hashtags, views in posts:
            for value in hashtags or []:
                tag = str(value).strip().lstrip("#").lower()
                if tag and term in tag:
                    post_count, view_count = counts.get(tag, (0, 0))
                    counts[tag] = (post_count + 1, view_count + (views or 0))
        return [
            HashtagResult(tag=tag, posts=post_count, views=view_count)
            for tag, (post_count, view_count) in sorted(
                counts.items(), key=lambda item: (-item[1][1], item[0])
            )[:page_size]
        ]

    @strawberry.field(name="trendingSounds")
    def trending_sounds(self, genre: str | None = None, limit: int = 50) -> list[SoundResult]:
        page_size = max(1, min(limit, 100))
        with get_session() as session:
            statement = select(DbSound).order_by(DbSound.rank, DbSound.total_plays.desc())
            if genre and genre != "All":
                statement = statement.where(DbSound.genre == genre)
            sounds = session.execute(statement.limit(page_size)).scalars().all()
            return [sound_to_graphql(sound) for sound in sounds]

    @strawberry.field(name="myPosts")
    def my_posts(self, info: Info) -> list[ContentItem]:
        user_id = info.context.get("user_id")
        if user_id is None:
            return []
        with get_session() as session:
            profile = session.execute(
                select(DbProfile).where(DbProfile.user_id == user_id)
            ).scalar_one_or_none()
            return [
                post_to_graphql(post)
                for post in profile.posts
            ] if profile else []

    @strawberry.field(name="myPlaylists")
    def my_playlists(self, info: Info) -> list[Playlist]:
        user_id = info.context.get("user_id")
        if user_id is None:
            return []
        with get_session() as session:
            profile = session.execute(
                select(DbProfile).where(DbProfile.user_id == user_id)
            ).scalar_one_or_none()
            return [
                Playlist(
                    id=str(item.id), title=item.title, cover=item.cover,
                    item_label=item.item_label, plays=item.plays,
                )
                for item in profile.playlists
            ] if profile else []

    @strawberry.field
    def followers(self, username: str) -> list[ProfileSummary]:
        with get_session() as session:
            profile = find_profile(session, username)
            if profile is None:
                return []
            profiles = session.execute(
                select(DbProfile)
                .join(Follow, Follow.follower_id == DbProfile.user_id)
                .where(Follow.following_id == profile.user_id)
            ).scalars().all()
            return [profile_summary(item) for item in profiles]

    @strawberry.field
    def following(self, username: str) -> list[ProfileSummary]:
        with get_session() as session:
            profile = find_profile(session, username)
            if profile is None:
                return []
            profiles = session.execute(
                select(DbProfile)
                .join(Follow, Follow.following_id == DbProfile.user_id)
                .where(Follow.follower_id == profile.user_id)
            ).scalars().all()
            return [profile_summary(item) for item in profiles]

    @strawberry.field(name="myFollowers")
    def my_followers(self, info: Info) -> list[ProfileSummary]:
        user_id = info.context.get("user_id")
        if user_id is None:
            return []
        with get_session() as session:
            profiles = session.execute(
                select(DbProfile)
                .join(Follow, Follow.follower_id == DbProfile.user_id)
                .where(Follow.following_id == user_id)
            ).scalars().all()
            return [profile_summary(item) for item in profiles]

    @strawberry.field(name="myFollowing")
    def my_following(self, info: Info) -> list[ProfileSummary]:
        user_id = info.context.get("user_id")
        if user_id is None:
            return []
        with get_session() as session:
            profiles = session.execute(
                select(DbProfile)
                .join(Follow, Follow.following_id == DbProfile.user_id)
                .where(Follow.follower_id == user_id)
            ).scalars().all()
            return [profile_summary(item) for item in profiles]

    @strawberry.field(name="myFollowersPage")
    def my_followers_page(self, info: Info, after: str | None = None, limit: int = 20) -> ProfilePage:
        user_id = info.context.get("user_id")
        return Query._follow_page(user_id, True, after, limit, viewer_id=user_id)

    @strawberry.field(name="myFollowingPage")
    def my_following_page(self, info: Info, after: str | None = None, limit: int = 20) -> ProfilePage:
        user_id = info.context.get("user_id")
        return Query._follow_page(user_id, False, after, limit, viewer_id=user_id)

    @strawberry.field(name="followersPage")
    def followers_page(self, username: str, info: Info, after: str | None = None, limit: int = 20) -> ProfilePage:
        with get_session() as session:
            profile = find_profile(session, username)
            if profile is None:
                return ProfilePage(profiles=[], next_cursor=None)
            user_id = profile.user_id
        return Query._follow_page(user_id, True, after, limit, viewer_id=info.context.get("user_id"))

    @strawberry.field(name="followingPage")
    def following_page(self, username: str, info: Info, after: str | None = None, limit: int = 20) -> ProfilePage:
        with get_session() as session:
            profile = find_profile(session, username)
            if profile is None:
                return ProfilePage(profiles=[], next_cursor=None)
            user_id = profile.user_id
        return Query._follow_page(user_id, False, after, limit, viewer_id=info.context.get("user_id"))

    @staticmethod
    def _follow_page(
        user_id: int | None, incoming: bool, after: str | None, limit: int, viewer_id: int | None = None,
    ) -> ProfilePage:
        if user_id is None:
            return ProfilePage(profiles=[], next_cursor=None)
        page_size = max(1, min(limit, 100))
        try:
            offset = max(0, int(after or "0"))
        except ValueError as error:
            raise api_error("Invalid follow cursor", "VALIDATION_ERROR", 400) from error
        with get_session() as session:
            join_column = Follow.follower_id if incoming else Follow.following_id
            owner_column = Follow.following_id if incoming else Follow.follower_id
            rows = session.execute(
                select(DbProfile)
                .join(Follow, join_column == DbProfile.user_id)
                .where(owner_column == user_id)
                .order_by(Follow.id)
                .offset(offset)
                .limit(page_size + 1)
            ).scalars().all()
            has_more = len(rows) > page_size
            rows = rows[:page_size]
            following_ids: set[int] = set()
            if viewer_id is not None and rows:
                following_ids = set(session.execute(
                    select(Follow.following_id).where(
                        Follow.follower_id == viewer_id,
                        Follow.following_id.in_([row.user_id for row in rows]),
                    )
                ).scalars().all())
            return ProfilePage(
                profiles=[
                    profile_summary(profile, is_following=profile.user_id in following_ids)
                    for profile in rows
                ],
                next_cursor=str(offset + page_size) if has_more else None,
            )

    @strawberry.field
    def feed(self, cursor: str | None = None, limit: int = 10) -> FeedPage:
        page_size = max(1, min(limit, 50))
        offset = 0
        if cursor:
            try:
                offset = max(0, int(cursor))
            except ValueError:
                raise api_error("Invalid feed cursor", "VALIDATION_ERROR", 400)

        with get_session() as session:
            rows = session.execute(
                select(DbPost, DbProfile)
                .join(DbProfile, DbPost.profile_id == DbProfile.id)
                .order_by(DbPost.id.desc())
                .offset(offset)
                .limit(page_size + 1)
            ).all()
            has_more = len(rows) > page_size
            rows = rows[:page_size]
            return FeedPage(
                items=[feed_item(post, profile) for post, profile in rows],
                next_cursor=str(offset + page_size) if has_more else None,
            )


@strawberry.type
class Mutation:
    @strawberry.field
    def update_profile(self, input: UpdateProfileInput, info: Info) -> Profile | None:
        """Update the logged-in user's profile. Only the owner can edit."""
        user_id = info.context.get("user_id")
        if user_id is None:
            raise api_error("Must be logged in to update profile", "UNAUTHENTICATED", 401)

        with get_session() as session:
            profile = session.execute(
                select(DbProfile).where(DbProfile.user_id == user_id)
            ).scalar_one_or_none()
            if profile is None:
                raise api_error("Profile not found", "NOT_FOUND", 404)

            if input.username is not None:
                username = input.username.strip().removeprefix("@").lower()
                if not re.fullmatch(r"[a-z0-9._]{3,24}", username):
                    raise api_error("Usernames are 3-24 characters: letters, numbers, dots and underscores.", "VALIDATION_ERROR", 400)
                taken = session.execute(
                    select(DbProfile).where(
                        DbProfile.username == username,
                        DbProfile.id != profile.id,
                    )
                ).scalar_one_or_none()
                if taken is not None:
                    raise api_error("That username is already taken.", "CONFLICT", 409)
                profile.username = username
            if input.display_name is not None:
                profile.display_name = input.display_name
            if input.bio is not None:
                profile.bio = input.bio
            if input.location is not None:
                profile.location = input.location
            if input.website is not None:
                profile.website = input.website
            if input.avatar_url is not None:
                profile.avatar_url = input.avatar_url
            if input.avatar_color is not None:
                profile.avatar_color = input.avatar_color
            if input.collab_status is not None:
                profile.collab_status = input.collab_status
            if input.open_to_collab is not None:
                profile.open_to_collab = input.open_to_collab

            session.commit()
            session.refresh(profile)
            return profile_to_graphql(profile)

    @strawberry.mutation
    def follow(self, username: str, info: Info) -> FollowResult:
        with get_session() as session:
            follower = owner_profile(session, info)
            target = find_profile(session, username)
            if target is None:
                raise api_error("Profile not found", "NOT_FOUND", 404)
            if target.user_id == follower.user_id:
                raise api_error("You cannot follow yourself", "VALIDATION_ERROR", 400)

            existing = session.execute(
                select(Follow).where(
                    Follow.follower_id == follower.user_id,
                    Follow.following_id == target.user_id,
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(Follow(
                    follower_id=follower.user_id,
                    following_id=target.user_id,
                ))
                follower.following += 1
                target.followers += 1
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    raise api_error("That follow already exists", "CONFLICT", 409)
            return FollowResult(
                following=True, followers=target.followers,
                following_count=follower.following,
            )

    @strawberry.mutation
    def unfollow(self, username: str, info: Info) -> FollowResult:
        with get_session() as session:
            follower = owner_profile(session, info)
            target = find_profile(session, username)
            if target is None:
                raise api_error("Profile not found", "NOT_FOUND", 404)

            existing = session.execute(
                select(Follow).where(
                    Follow.follower_id == follower.user_id,
                    Follow.following_id == target.user_id,
                )
            ).scalar_one_or_none()
            if existing is not None:
                session.delete(existing)
                follower.following = max(0, follower.following - 1)
                target.followers = max(0, target.followers - 1)
                session.commit()
            return FollowResult(
                following=False, followers=target.followers,
                following_count=follower.following,
            )

    @strawberry.mutation(name="createPost")
    def create_post(self, input: PostInput, info: Info) -> ContentItem:
        with get_session() as session:
            profile = owner_profile(session, info)
            media = owned_media(session, profile.user_id, input.media_id, "Media ID")
            thumbnail_media = owned_media(session, profile.user_id, input.thumbnail_media_id, "Thumbnail media ID")
            if not thumbnail_media.content_type.startswith("image/"):
                raise api_error("Thumbnail must be an image", "VALIDATION_ERROR", 400)
            post = DbPost(
                profile_id=profile.id,
                thumbnail=thumbnail_media.url,
                media_url=media.url,
                media_id=media.id,
                thumbnail_media_id=thumbnail_media.id,
                caption=input.caption,
                collab_with=input.collab_with,
                hashtags=input.hashtags,
                audio=input.audio,
                visibility=input.visibility,
                allow_comments=input.allow_comments,
                allow_collabs=input.allow_collabs,
                duration_sec=input.duration_sec,
            )
            session.add(post)
            session.commit()
            session.refresh(post)
            return post_to_graphql(post)

    @strawberry.mutation(name="updatePost")
    def update_post(self, id: strawberry.ID, input: UpdatePostInput, info: Info) -> ContentItem:
        with get_session() as session:
            profile = owner_profile(session, info)
            post_id = parse_int_id(id, "Post ID")
            post = session.execute(
                select(DbPost).where(DbPost.id == post_id, DbPost.profile_id == profile.id)
            ).scalar_one_or_none()
            if post is None:
                raise api_error("Post not found", "NOT_FOUND", 404)
            if input.caption is not None:
                post.caption = input.caption
            if input.collab_with is not None:
                post.collab_with = input.collab_with
            if input.hashtags is not None:
                post.hashtags = input.hashtags
            if input.audio is not None:
                post.audio = input.audio
            if input.visibility is not None:
                post.visibility = input.visibility
            if input.allow_comments is not None:
                post.allow_comments = input.allow_comments
            if input.allow_collabs is not None:
                post.allow_collabs = input.allow_collabs
            if input.duration_sec is not None:
                post.duration_sec = input.duration_sec
            session.commit()
            session.refresh(post)
            return post_to_graphql(post)

    @strawberry.mutation(name="deletePost")
    def delete_post(self, id: strawberry.ID, info: Info) -> bool:
        with get_session() as session:
            profile = owner_profile(session, info)
            post_id = parse_int_id(id, "Post ID")
            post = session.execute(
                select(DbPost).where(DbPost.id == post_id, DbPost.profile_id == profile.id)
            ).scalar_one_or_none()
            if post is None:
                return False
            session.delete(post)
            session.commit()
            return True

    @strawberry.mutation(name="createPlaylist")
    def create_playlist(self, input: PlaylistInput, info: Info) -> Playlist:
        with get_session() as session:
            profile = owner_profile(session, info)
            playlist = DbPlaylist(
                profile_id=profile.id, title=input.title, cover=input.cover,
                item_label=input.item_label,
            )
            session.add(playlist)
            session.commit()
            session.refresh(playlist)
            return Playlist(
                id=str(playlist.id), title=playlist.title, cover=playlist.cover,
                item_label=playlist.item_label, plays=playlist.plays,
            )

    @strawberry.mutation(name="updatePlaylist")
    def update_playlist(self, id: strawberry.ID, input: UpdatePlaylistInput, info: Info) -> Playlist:
        with get_session() as session:
            profile = owner_profile(session, info)
            playlist_id = parse_int_id(id, "Playlist ID")
            playlist = session.execute(
                select(DbPlaylist).where(
                    DbPlaylist.id == playlist_id, DbPlaylist.profile_id == profile.id
                )
            ).scalar_one_or_none()
            if playlist is None:
                raise api_error("Playlist not found", "NOT_FOUND", 404)
            if input.title is not None:
                playlist.title = input.title
            if input.cover is not None:
                playlist.cover = input.cover
            if input.item_label is not None:
                playlist.item_label = input.item_label
            session.commit()
            session.refresh(playlist)
            return Playlist(
                id=str(playlist.id), title=playlist.title, cover=playlist.cover,
                item_label=playlist.item_label, plays=playlist.plays,
            )

    @strawberry.mutation(name="deletePlaylist")
    def delete_playlist(self, id: strawberry.ID, info: Info) -> bool:
        with get_session() as session:
            profile = owner_profile(session, info)
            playlist_id = parse_int_id(id, "Playlist ID")
            playlist = session.execute(
                select(DbPlaylist).where(
                    DbPlaylist.id == playlist_id, DbPlaylist.profile_id == profile.id
                )
            ).scalar_one_or_none()
            if playlist is None:
                return False
            session.delete(playlist)
            session.commit()
            return True


schema = strawberry.Schema(query=Query, mutation=Mutation)


def get_context_for_request(request: Request):
    """Extract user_id from session and pass to GraphQL context."""
    user_id = request.session.get("user_id")
    return {"user_id": user_id, "request": request}


graphql_app = GraphQLRouter(schema, context_getter=get_context_for_request)
app = FastAPI(title="ConnextionZ Profile API")

rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in {"0", "false", "no"}
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=rate_limit_enabled,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

environment = os.getenv("ENVIRONMENT", "development").lower()
session_secret = os.getenv("SESSION_SECRET")
if not session_secret:
    if environment == "production":
        raise RuntimeError("SESSION_SECRET must be set in production")
    session_secret = "local-development-session-secret"

session_cookie_secure = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
session_same_site = os.getenv("SESSION_COOKIE_SAMESITE", "lax").lower()
if session_same_site not in {"lax", "strict", "none"}:
    raise RuntimeError("SESSION_COOKIE_SAMESITE must be lax, strict, or none")
if session_same_site == "none" and not session_cookie_secure:
    raise RuntimeError("SESSION_COOKIE_SECURE must be true when SESSION_COOKIE_SAMESITE is none")

session_max_age = int(os.getenv("SESSION_MAX_AGE", str(60 * 60 * 24 * 7)))

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="connextionz_session",
    max_age=session_max_age,
    same_site=session_same_site,
    https_only=session_cookie_secure,
)

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
if not cors_origins:
    if environment == "production":
        raise RuntimeError("CORS_ORIGINS must be set in production")
    cors_origins = [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

allowed_hosts = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

if os.getenv("REQUIRE_HTTPS", "false").lower() in {"1", "true", "yes"}:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.1f client=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request.client.host if request.client else "unknown",
    )
    return response

app.include_router(graphql_app, prefix="/graphql")
app.include_router(create_media_router(limiter))


app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")
app.include_router(create_auth_router(limiter))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
