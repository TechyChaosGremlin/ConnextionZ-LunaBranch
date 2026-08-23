from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Post, Playlist, Profile, User


def seed_database() -> None:
    with Session(engine) as session:
        if session.execute(select(User)).first() is not None:
            return

        user = User(email="demo@connextionz.app", password_hash="demo")
        session.add(user)
        session.flush()

        profile = Profile(
            user_id=user.id,
            username="luna",
            display_name="Luna Hart",
            avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=256&h=256&fit=crop&auto=format",
            avatar_color="#7c3aed",
            bio="I make cinematic short-form visuals and electronic soundscapes.",
            location="Brooklyn, NY",
            website="lunahart.studio",
            verified=True,
            online=True,
            collab_status="Available for Collaboration",
            collab_score=94.0,
            collab_count=17,
            followers=48200,
            following=621,
            open_to_collab=True,
            private_account=False,
            response_time="< 4 hours",
        )
        session.add(profile)
        session.flush()

        session.add_all(
            [
                Post(
                    profile_id=profile.id,
                    thumbnail="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400&h=711&fit=crop&auto=format",
                    caption="Late night studio sessions always hit different 🎵 new track dropping this Friday",
                    views=1284000,
                    likes=284700,
                    collab_with="nova.dj",
                ),
                Post(
                    profile_id=profile.id,
                    thumbnail="https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=711&fit=crop&auto=format",
                    caption="Golden hour was NOT messing around today 📸 caught the whole shift in one frame",
                    views=2140000,
                    likes=531200,
                    collab_with=None,
                ),
            ]
        )

        session.add_all(
            [
                Playlist(
                    profile_id=profile.id,
                    title="Night Mode Sessions",
                    cover="https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=400&fit=crop&auto=format",
                    item_label="12 tracks",
                    plays=41800,
                ),
                Playlist(
                    profile_id=profile.id,
                    title="Golden Hour Frames",
                    cover="https://images.unsplash.com/photo-1504704911898-68304a7d2807?w=400&h=400&fit=crop&auto=format",
                    item_label="9 edits",
                    plays=27100,
                ),
            ]
        )

        session.commit()
