from __future__ import annotations

import strawberry
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from backend.app.database import UserProfile, engine


@strawberry.type
class ContentItem:
    id: str
    thumbnail: str
    caption: str
    views: int
    likes: int
    collab_with: str | None = strawberry.field(name="collabWith")


@strawberry.type
class Playlist:
    id: str
    title: str
    cover: str
    item_label: str = strawberry.field(name="itemLabel")
    plays: int


@strawberry.type
class Profile:
    id: str
    username: str
    display_name: str = strawberry.field(name="displayName")
    avatar_url: str = strawberry.field(name="avatarUrl")
    avatar_color: str = strawberry.field(name="avatarColor")
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    verified: bool = False
    online: bool = True
    collab_status: str | None = strawberry.field(name="collabStatus")
    collab_score: int = strawberry.field(name="collabScore")
    collab_count: int = strawberry.field(name="collabCount")
    followers: int = 0
    following: int = 0
    open_to_collab: bool = strawberry.field(name="openToCollab")
    response_time: str = strawberry.field(name="responseTime")
    posts: list[ContentItem]
    playlists: list[Playlist]


@strawberry.input
class UpdateProfileInput:
    display_name: str | None = strawberry.field(name="displayName")
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    avatar_url: str | None = strawberry.field(name="avatarUrl")
    collab_status: str | None = strawberry.field(name="collabStatus")
    open_to_collab: bool | None = strawberry.field(name="openToCollab")


POSTS = [
    ContentItem(
        id="1",
        thumbnail="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400&h=711&fit=crop&auto=format",
        caption="Late night studio sessions always hit different 🎵 new track dropping this Friday",
        views=1284000,
        likes=284700,
        collab_with="nova.dj",
    ),
    ContentItem(
        id="2",
        thumbnail="https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=711&fit=crop&auto=format",
        caption="Golden hour was NOT messing around today 📸 caught the whole shift in one frame",
        views=2140000,
        likes=531200,
        collab_with=None,
    ),
]

PLAYLISTS = [
    Playlist(
        id="p1",
        title="Night Mode Sessions",
        cover="https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=400&fit=crop&auto=format",
        item_label="12 tracks",
        plays=41800,
    ),
    Playlist(
        id="p2",
        title="Golden Hour Frames",
        cover="https://images.unsplash.com/photo-1504704911898-68304a7d2807?w=400&h=400&fit=crop&auto=format",
        item_label="9 edits",
        plays=27100,
    ),
]


def load_profile_from_db(username: str | None = None) -> UserProfile | None:
    with Session(engine) as session:
        stmt = select(UserProfile)
        if username is not None:
            stmt = stmt.where(UserProfile.username == username)
        result = session.execute(stmt).scalars().first()
        return result


def profile_to_graphql(profile: UserProfile) -> Profile:
    return Profile(
        id=str(profile.id),
        username=profile.username,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url or "",
        avatar_color=profile.avatar_color or "#7c3aed",
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
        posts=POSTS,
        playlists=PLAYLISTS,
    )


@strawberry.type
class Query:
    @strawberry.field
    def me(self) -> Profile | None:
        profile = load_profile_from_db("luna")
        return profile_to_graphql(profile) if profile else None

    @strawberry.field
    def profile(self, username: str) -> Profile | None:
        profile = load_profile_from_db(username)
        return profile_to_graphql(profile) if profile else None


@strawberry.type
class Mutation:
    @strawberry.field
    def update_profile(self, input: UpdateProfileInput) -> Profile | None:
        profile = load_profile_from_db("luna")
        if profile is None:
            return None

        with Session(engine) as session:
            existing = session.get(UserProfile, profile.id)
            if existing is None:
                return None

            if input.display_name is not None:
                existing.display_name = input.display_name
            if input.bio is not None:
                existing.bio = input.bio
            if input.location is not None:
                existing.location = input.location
            if input.website is not None:
                existing.website = input.website
            if input.avatar_url is not None:
                existing.avatar_url = input.avatar_url
            if input.collab_status is not None:
                existing.collab_status = input.collab_status
            if input.open_to_collab is not None:
                existing.open_to_collab = input.open_to_collab

            session.commit()
            session.refresh(existing)

        updated = load_profile_from_db("luna")
        return profile_to_graphql(updated) if updated else None


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app = FastAPI(title="ConnextionZ Profile API")
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
