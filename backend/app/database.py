from __future__ import annotations

from sqlalchemy import create_engine, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

DATABASE_URL = "sqlite:///./profiles.db"


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    online: Mapped[bool] = mapped_column(Boolean, default=True)
    collab_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    collab_score: Mapped[int] = mapped_column(Integer, default=0)
    collab_count: Mapped[int] = mapped_column(Integer, default=0)
    followers: Mapped[int] = mapped_column(Integer, default=0)
    following: Mapped[int] = mapped_column(Integer, default=0)
    open_to_collab: Mapped[bool] = mapped_column(Boolean, default=True)
    response_time: Mapped[str] = mapped_column(String(50), default="< 4 hours")


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)


def seed_profiles() -> None:
    with Session(engine) as session:
        if session.query(UserProfile).count() > 0:
            return

        session.add_all(
            [
                UserProfile(
                    id=1,
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
                    collab_score=94,
                    collab_count=17,
                    followers=48200,
                    following=621,
                    open_to_collab=True,
                    response_time="< 4 hours",
                ),
                UserProfile(
                    id=2,
                    username="milo",
                    display_name="Milo Ross",
                    avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=256&h=256&fit=crop&auto=format",
                    avatar_color="#0ea5e9",
                    bio="Photographer and motion storyteller.",
                    location="Los Angeles, CA",
                    website="miloross.studio",
                    verified=False,
                    online=True,
                    collab_status="Open for branded shoots",
                    collab_score=88,
                    collab_count=12,
                    followers=18340,
                    following=410,
                    open_to_collab=True,
                    response_time="< 8 hours",
                ),
            ]
        )
        session.commit()


seed_profiles()
