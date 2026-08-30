"""
Tests for the Following/For-You feed and follow/unfollow behavior.

Covers the checklist:
- Follow a creator -> their posts appear in the Following feed.
- Unfollow -> their posts disappear from the Following feed.
- Following feed and For You feed remain separate result sets.
- Feed pagination (cursor/limit) works.

Follows the pattern established in test_social_interactions.py: resolvers are
called directly with a lightweight AppContext, and repository methods are
monkeypatched so no real (Postgres-only) database is required. The follow
graph is backed by an in-memory dict shared across the monkeypatched
FollowRepository methods, so `_follow`/`_unfollow` really change what `_feed`
returns.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from api.graphql import AppContext, _feed, _follow, _unfollow
from app.models.content import ContentStatus
from app.models.user import AccountStatus, User, UserRole


def make_user(username: str) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{username}@example.com",
        username=username,
        hashed_password="hashed",
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        email_verified=True,
        mfa_enabled=False,
    )


def make_profile(user: User) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name=user.username,
        avatar_url="",
        avatar_color="#00AEEF",
        verified=False,
        collab_score=0.0,
        collaboration_count=0,
        follower_count=0,
        following_count=0,
        open_to_collab=True,
        private_account=False,
    )


def make_post(user_id: uuid.UUID, post_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=post_id,
        user_id=user_id,
        thumbnail="",
        media_url=None,
        caption="hello",
        view_count=0,
        like_count=0,
        collab_with=None,
        hashtags=[],
        audio="Original Sound",
        visibility="public",
        allow_comments=True,
        allow_collabs=True,
        duration_sec=0.0,
        comment_count=0,
        share_count=0,
        save_count=0,
        status=ContentStatus.PUBLISHED,
        scheduled_at=None,
    )


def make_ctx(user: User) -> AppContext:
    return AppContext(db=AsyncMock(), current_user=user)


class FakeFollowGraph:
    """In-memory follower/following graph shared by monkeypatched FollowRepository methods.

    Methods here take the same arguments callers pass to FollowRepository (no
    leading `self`) so they can also be called directly from tests.
    """

    def __init__(self):
        self.edges: set[tuple[uuid.UUID, uuid.UUID]] = set()

    async def follow(self, follower_id, following_id):
        self.edges.add((follower_id, following_id))

    async def unfollow(self, follower_id, following_id):
        self.edges.discard((follower_id, following_id))

    async def is_following(self, follower_id, following_id):
        return (follower_id, following_id) in self.edges

    async def get_following_ids(self, follower_id):
        return [b for (a, b) in self.edges if a == follower_id]

    async def count_followers(self, user_id):
        return sum(1 for (_, b) in self.edges if b == user_id)

    async def count_following(self, user_id):
        return sum(1 for (a, _) in self.edges if a == user_id)


@pytest.fixture
def follow_graph(monkeypatch):
    graph = FakeFollowGraph()
    monkeypatch.setattr(
        "repositories.social_repository.FollowRepository.follow",
        lambda self, follower_id, following_id: graph.follow(follower_id, following_id),
    )
    monkeypatch.setattr(
        "repositories.social_repository.FollowRepository.unfollow",
        lambda self, follower_id, following_id: graph.unfollow(follower_id, following_id),
    )
    monkeypatch.setattr(
        "repositories.social_repository.FollowRepository.is_following",
        lambda self, follower_id, following_id: graph.is_following(follower_id, following_id),
    )
    monkeypatch.setattr(
        "repositories.social_repository.FollowRepository.get_following_ids",
        lambda self, follower_id: graph.get_following_ids(follower_id),
    )
    monkeypatch.setattr(
        "repositories.social_repository.FollowRepository.count_followers",
        lambda self, user_id: graph.count_followers(user_id),
    )
    monkeypatch.setattr(
        "repositories.social_repository.FollowRepository.count_following",
        lambda self, user_id: graph.count_following(user_id),
    )
    return graph


@pytest.fixture(autouse=True)
def stub_shared_dependencies(monkeypatch):
    """Neutralize interaction/profile/notification lookups unrelated to feed filtering."""

    async def fake_get_hidden_creator_ids(self, viewer_id, creator_ids):
        return set()

    monkeypatch.setattr(
        "repositories.social_repository.FeedSafetyRepository.get_hidden_creator_ids",
        fake_get_hidden_creator_ids,
    )

    async def fake_has_interaction(self, post_id, user_id):
        return False

    monkeypatch.setattr("repositories.social_repository.PostInteractionRepository.has_liked", fake_has_interaction)
    monkeypatch.setattr("repositories.social_repository.PostInteractionRepository.has_saved", fake_has_interaction)
    monkeypatch.setattr("repositories.social_repository.PostInteractionRepository.has_shared", fake_has_interaction)

    async def fake_get_profile_by_user_id(self, user_id):
        return make_profile(SimpleNamespace(id=user_id, username="creator"))

    monkeypatch.setattr(
        "repositories.profile_repository.ProfileRepository.get_by_user_id", fake_get_profile_by_user_id
    )

    async def fake_user_get_by_id(self, entity_id):
        return make_user("creator")

    monkeypatch.setattr("repositories.user_repository.UserRepository.get_by_id", fake_user_get_by_id)

    async def fake_create_notification(self, **kwargs):
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(
        "repositories.notification_repository.NotificationRepository.create_notification",
        fake_create_notification,
    )

    async def fake_record_signal(self, **kwargs):
        return None

    monkeypatch.setattr("repositories.analytics_repository.AnalyticsRepository.record", fake_record_signal)


def stub_feed_posts(monkeypatch, posts: list[SimpleNamespace]):
    """Patch PostRepository.get_feed to emulate DB filtering/ordering/pagination over `posts`."""

    async def fake_get_feed(self, user_ids, content_types=None, limit=20, before_id=None):
        candidates = [p for p in posts if p.user_id in user_ids]
        candidates.sort(key=lambda p: p.id, reverse=True)
        if before_id is not None:
            candidates = [p for p in candidates if p.id < before_id]
        return candidates[:limit]

    monkeypatch.setattr("repositories.content_repository.PostRepository.get_feed", fake_get_feed)


def stub_hidden_creators(monkeypatch, creator_ids: set[uuid.UUID] | None = None):
    async def fake_get_hidden_creator_ids(self, viewer_id, candidate_ids):
        return creator_ids or set()

    monkeypatch.setattr(
        "repositories.social_repository.FeedSafetyRepository.get_hidden_creator_ids",
        fake_get_hidden_creator_ids,
    )


def _ordered_post_ids(n: int) -> list[uuid.UUID]:
    """Generate UUIDs that sort in creation order (like time-sortable UUIDv7 ids)."""
    return sorted(uuid.uuid4() for _ in range(n))


@pytest.mark.asyncio
async def test_follow_creator_then_their_posts_appear_in_following_feed(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    creator = make_user("creator")

    post_id = _ordered_post_ids(1)[0]
    stub_feed_posts(monkeypatch, [make_post(creator.id, post_id)])

    async def fake_get_by_username(self, username):
        return creator

    monkeypatch.setattr("repositories.user_repository.UserRepository.get_by_username", fake_get_by_username)

    ctx = make_ctx(viewer)

    # Before following: creator's posts do not show up in the Following feed.
    page_before = await _feed(ctx, cursor=None, limit=10, following=True)
    assert page_before.items == []

    # Follow the creator.
    await _follow(ctx, creator.username)
    assert await follow_graph.is_following(viewer.id, creator.id)

    # After following: creator's post appears in the Following feed.
    page_after = await _feed(ctx, cursor=None, limit=10, following=True)
    assert [item.id for item in page_after.items] == [post_id]


@pytest.mark.asyncio
async def test_unfollow_makes_creator_posts_disappear_from_following_feed(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    creator = make_user("creator")

    post_id = _ordered_post_ids(1)[0]
    stub_feed_posts(monkeypatch, [make_post(creator.id, post_id)])

    async def fake_get_by_username(self, username):
        return creator

    monkeypatch.setattr("repositories.user_repository.UserRepository.get_by_username", fake_get_by_username)

    ctx = make_ctx(viewer)

    await _follow(ctx, creator.username)
    page_following = await _feed(ctx, cursor=None, limit=10, following=True)
    assert [item.id for item in page_following.items] == [post_id]

    await _unfollow(ctx, creator.username)
    assert not await follow_graph.is_following(viewer.id, creator.id)

    page_after_unfollow = await _feed(ctx, cursor=None, limit=10, following=True)
    assert page_after_unfollow.items == []


@pytest.mark.asyncio
async def test_following_feed_and_for_you_feed_are_separate(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    followed = make_user("followed")
    stranger = make_user("stranger")

    followed_post_id, stranger_post_id, own_post_id = _ordered_post_ids(3)
    stub_feed_posts(
        monkeypatch,
        [
            make_post(followed.id, followed_post_id),
            make_post(stranger.id, stranger_post_id),
            make_post(viewer.id, own_post_id),
        ],
    )

    await follow_graph.follow(viewer.id, followed.id)

    ctx = make_ctx(viewer)

    following_page = await _feed(ctx, cursor=None, limit=10, following=True)
    for_you_page = await _feed(ctx, cursor=None, limit=10, following=False)

    following_ids = {item.id for item in following_page.items}
    for_you_ids = {item.id for item in for_you_page.items}

    # Following feed only contains posts from followed creators.
    assert following_ids == {followed_post_id}

    # For You feed includes the viewer's own posts and followed creators, but
    # never a stranger's posts, and is not identical to the Following feed
    # (it additionally includes the viewer's own content).
    assert for_you_ids == {followed_post_id, own_post_id}
    assert stranger_post_id not in for_you_ids
    assert stranger_post_id not in following_ids
    assert for_you_ids != following_ids


@pytest.mark.asyncio
async def test_feed_pagination_returns_next_cursor_and_subsequent_page(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    creator = make_user("creator")

    post_ids = _ordered_post_ids(3)  # oldest -> newest
    stub_feed_posts(monkeypatch, [make_post(creator.id, pid) for pid in post_ids])

    await follow_graph.follow(viewer.id, creator.id)
    ctx = make_ctx(viewer)

    first_page = await _feed(ctx, cursor=None, limit=2, following=True)
    # Newest-first ordering, limited to 2 of the 3 posts, with a cursor for more.
    assert [item.id for item in first_page.items] == [post_ids[2], post_ids[1]]
    assert first_page.next_cursor == str(post_ids[1])

    second_page = await _feed(ctx, cursor=first_page.next_cursor, limit=2, following=True)
    assert [item.id for item in second_page.items] == [post_ids[0]]
    assert second_page.next_cursor is None


@pytest.mark.asyncio
async def test_feed_excludes_hidden_deleted_and_unapproved_creator_posts(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    visible_creator = make_user("visible")
    blocked_creator = make_user("blocked")
    muted_creator = make_user("muted")
    deleted_creator = make_user("deleted")
    moderated_creator = make_user("moderated")
    post_ids = _ordered_post_ids(5)
    posts = [
        make_post(visible_creator.id, post_ids[0]),
        make_post(blocked_creator.id, post_ids[1]),
        make_post(muted_creator.id, post_ids[2]),
        make_post(deleted_creator.id, post_ids[3]),
        make_post(moderated_creator.id, post_ids[4]),
    ]
    posts[3].status = ContentStatus.REMOVED
    posts[4].moderation_status = "under_review"
    stub_feed_posts(monkeypatch, posts)
    stub_hidden_creators(monkeypatch, {blocked_creator.id, muted_creator.id})
    for creator in (visible_creator, blocked_creator, muted_creator, deleted_creator, moderated_creator):
        await follow_graph.follow(viewer.id, creator.id)

    page = await _feed(make_ctx(viewer), cursor=None, limit=10, following=True)

    assert [item.id for item in page.items] == [post_ids[0]]


@pytest.mark.asyncio
async def test_feed_enforces_private_and_post_visibility_rules(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    public_creator = make_user("public")
    private_creator = make_user("private")
    follower_only_creator = make_user("followers")
    post_ids = _ordered_post_ids(4)
    public_post = make_post(public_creator.id, post_ids[0])
    private_post = make_post(public_creator.id, post_ids[1])
    private_post.visibility = "private"
    account_private_post = make_post(private_creator.id, post_ids[2])
    follower_post = make_post(follower_only_creator.id, post_ids[3])
    follower_post.visibility = "followers"
    stub_feed_posts(monkeypatch, [public_post, private_post, account_private_post, follower_post])
    stub_hidden_creators(monkeypatch)

    async def fake_profile(self, user_id):
        return SimpleNamespace(
            id=uuid.uuid4(),
            user_id=user_id,
            display_name="creator",
            avatar_url="",
            avatar_color="#00AEEF",
            verified=False,
            collab_score=0.0,
            collaboration_count=0,
            follower_count=0,
            following_count=0,
            open_to_collab=True,
            private_account=user_id == private_creator.id,
        )

    monkeypatch.setattr("repositories.profile_repository.ProfileRepository.get_by_user_id", fake_profile)
    await follow_graph.follow(viewer.id, public_creator.id)
    await follow_graph.follow(viewer.id, follower_only_creator.id)

    page = await _feed(make_ctx(viewer), cursor=None, limit=10, following=False)

    assert {item.id for item in page.items} == {post_ids[0], post_ids[3]}


@pytest.mark.asyncio
async def test_feed_preserves_comment_and_collaboration_settings(monkeypatch, follow_graph):
    viewer = make_user("viewer")
    creator = make_user("creator")
    post_id = _ordered_post_ids(1)[0]
    post = make_post(creator.id, post_id)
    post.allow_comments = False
    post.allow_collabs = False
    stub_feed_posts(monkeypatch, [post])
    stub_hidden_creators(monkeypatch)
    await follow_graph.follow(viewer.id, creator.id)

    page = await _feed(make_ctx(viewer), cursor=None, limit=10, following=True)

    assert page.items[0].allow_comments is False
    assert page.items[0].allow_collabs is False
