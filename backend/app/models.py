from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    online: Mapped[bool] = mapped_column(Boolean, default=True)

    collab_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    collab_score: Mapped[float] = mapped_column(Float, default=0.0)
    collab_count: Mapped[int] = mapped_column(Integer, default=0)
    followers: Mapped[int] = mapped_column(Integer, default=0)
    following: Mapped[int] = mapped_column(Integer, default=0)

    open_to_collab: Mapped[bool] = mapped_column(Boolean, default=True)
    response_time: Mapped[str] = mapped_column(String(50), default="< 4 hours")

    user: Mapped[User] = relationship(back_populates="profile")
    posts: Mapped[list["Post"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    playlists: Mapped[list["Playlist"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class Follow(Base):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follows_pair"),
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)

    thumbnail: Mapped[str] = mapped_column(String(500), nullable=False)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    audio: Mapped[str] = mapped_column(String(255), default="Original Sound")
    visibility: Mapped[str] = mapped_column(String(20), default="public")
    allow_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_collabs: Mapped[bool] = mapped_column(Boolean, default=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    collab_with: Mapped[str | None] = mapped_column(String(120), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="posts")


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    cover: Mapped[str] = mapped_column(String(500), nullable=False)
    item_label: Mapped[str] = mapped_column(String(80), nullable=False)
    plays: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped[Profile] = relationship(back_populates="playlists")
