from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from api.graphql import AppContext, _search
from app.models.user import AccountStatus, User, UserRole


@pytest.mark.asyncio
async def test_user_search_accepts_string_type_filters(monkeypatch):
    user = User(
        id="11111111-1111-4111-8111-111111111111",
        email="alice@example.com",
        username="alice",
        hashed_password="hashed",
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        email_verified=True,
        mfa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    ctx = AppContext(db=object(), current_user=user)
    assert ctx.user is user

    async def fake_user_search(self, query, limit=20, offset=0):
        assert query == "alice"
        assert limit == 6
        return [(user, 88.0)]

    async def fake_post_search(*args, **kwargs):
        raise AssertionError("posts should not be searched when type filter is USER")

    monkeypatch.setattr(
        "repositories.user_repository.UserRepository.search_by_username_and_display_name",
        fake_user_search,
    )
    monkeypatch.setattr(
        "repositories.content_repository.PostRepository.search_by_content",
        fake_post_search,
    )

    result = await _search(ctx, SimpleNamespace(query="alice", types=["USER"]), 20, None)

    assert len(result.edges) == 1
    assert result.total_count == 1
    assert result.edges[0].node.type == "USER"
    assert result.edges[0].node.user.username == "alice"


@pytest.mark.asyncio
async def test_user_search_accepts_enum_like_type_filters(monkeypatch):
    user = User(
        id="22222222-2222-4222-8222-222222222222",
        email="bob@example.com",
        username="bob",
        hashed_password="hashed",
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        email_verified=True,
        mfa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    ctx = AppContext(db=object(), current_user=user)

    class SearchType:
        def __init__(self, value):
            self.value = value

    async def fake_user_search(self, query, limit=20, offset=0):
        return [(user, 77.0)]

    async def fake_post_search(*args, **kwargs):
        raise AssertionError("posts should not be searched when type filter is USER")

    monkeypatch.setattr(
        "repositories.user_repository.UserRepository.search_by_username_and_display_name",
        fake_user_search,
    )
    monkeypatch.setattr(
        "repositories.content_repository.PostRepository.search_by_content",
        fake_post_search,
    )

    result = await _search(ctx, SimpleNamespace(query="bob", types=[SearchType("USER")]), 20, None)

    assert len(result.edges) == 1
    assert result.total_count == 1
    assert result.edges[0].node.type == "USER"


@pytest.mark.asyncio
async def test_search_posts_returns_legacy_feed_page_shape(monkeypatch):
    user = User(
        id="33333333-3333-4333-8333-333333333333",
        email="charlie@example.com",
        username="charlie",
        hashed_password="hashed",
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        email_verified=True,
        mfa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    ctx = AppContext(db=object(), current_user=user)

    post = SimpleNamespace(
        id="44444444-4444-4444-8444-444444444444",
        user_id=user.id,
        caption="Launch day in Berlin",
        hashtags=["launch", "berlin"],
        audio="Original Sound",
        visibility="public",
        allow_comments=True,
        allow_collabs=True,
        duration_sec=12.5,
        like_count=10,
        comment_count=2,
        share_count=1,
        view_count=99,
        save_count=0,
        collab_with=None,
        thumbnail="",
        media_url="",
        status=SimpleNamespace(value="published"),
        scheduled_at=None,
    )
    profile = SimpleNamespace(
        id="55555555-5555-4555-8555-555555555555",
        user_id=user.id,
        display_name="Charlie Launch",
        avatar_url="",
        avatar_color="#00AEEF",
        verified=False,
        collab_score=0.0,
        collaboration_count=0,
        follower_count=12,
        following_count=7,
        open_to_collab=True,
        private_account=False,
    )

    async def fake_search(self, query, limit=20, offset=0):
        assert query == "launch"
        assert limit == 21
        return [(post, profile, 42.0)]

    monkeypatch.setattr(
        "repositories.content_repository.PostRepository.search_by_content",
        fake_search,
    )

    from api.graphql import Query

    result = await Query().search_posts(SimpleNamespace(context=ctx), "launch", None, 20, None, "relevance")

    assert result.items[0].caption == "Launch day in Berlin"
    assert result.items[0].creator.username == "charlie"
    assert result.items[0].creator.display_name == "Charlie Launch"
