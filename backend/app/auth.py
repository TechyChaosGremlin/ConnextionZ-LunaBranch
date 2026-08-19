from __future__ import annotations

import re

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.models import User, Profile


class AuthContext:
    """Auth context passed to GraphQL resolvers via Strawberry."""
    def __init__(self, user_id: int | None = None, username: str | None = None):
        self.user_id = user_id
        self.username = username

    @staticmethod
    def from_session(session_user_id: int | None) -> AuthContext:
        return AuthContext(user_id=session_user_id)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    if not stored_hash.startswith("$2"):
        return stored_hash == password
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        return False


def authenticate_user(email: str, password: str) -> User | None:
    """Verify bcrypt credentials and upgrade an existing legacy password."""
    email = email.strip().lower()
    with get_session() as session:
        user = session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user and verify_password(password, user.password_hash):
            if user.password_hash and not user.password_hash.startswith("$2"):
                user.password_hash = hash_password(password)
                session.commit()
            return user
    return None


def register_user(
    email: str,
    password: str,
    username: str,
    display_name: str,
) -> tuple[User, Profile] | None:
    """Create a new user and profile. Returns (user, profile) or None if email exists."""
    email = email.strip().lower()
    username = username.strip().removeprefix("@").lower()
    display_name = display_name.strip()
    if not re.fullmatch(r"[a-z0-9._]{3,24}", username) or not display_name:
        return None

    with get_session() as session:
        existing = session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        existing_profile = session.execute(
            select(Profile).where(Profile.username == username)
        ).scalar_one_or_none()
        if existing or existing_profile:
            return None

        user = User(email=email, password_hash=hash_password(password))
        session.add(user)
        session.flush()

        profile = Profile(
            user_id=user.id,
            username=username,
            display_name=display_name,
            bio="",
            location="",
            website="",
            avatar_color="#00AEEF",
            verified=False,
            online=True,
            collab_status="Open to Collaboration",
            collab_score=0.0,
            collab_count=0,
            followers=0,
            following=0,
            open_to_collab=True,
            private_account=False,
            response_time="< 4 hours",
        )
        session.add(profile)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return None
        session.refresh(user)
        session.refresh(profile)

        return (user, profile)


def get_user_profile(user_id: int) -> Profile | None:
    """Fetch a user's profile by user ID."""
    with get_session() as session:
        profile = session.execute(
            select(Profile)
            .options(selectinload(Profile.posts), selectinload(Profile.playlists))
            .where(Profile.user_id == user_id)
        ).scalar_one_or_none()
        return profile


def delete_user_account(user_id: int) -> bool:
    """Delete a user account and all related ORM-owned records."""
    with get_session() as session:
        user = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        if user is None:
            return False
        session.delete(user)
        session.commit()
        return True
