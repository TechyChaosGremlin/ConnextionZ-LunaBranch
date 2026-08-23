"""
Tests for JWT token management.

Validates:
- Token creation
- Token validation
- Token expiration
- Token blacklisting (placeholder)
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from features.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_payload,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)
from app.models.user import User, UserRole


@pytest.fixture
def test_user():
    """Create a test user for token generation."""
    return User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        role=UserRole.USER,
        status="active",
    )


def test_create_access_token(test_user):
    """Test that access token is created correctly."""
    token = create_access_token(test_user)

    assert token is not None
    assert isinstance(token, str)

    # Decode and verify payload
    payload = decode_token(token)
    assert payload["sub"] == "test-user-id"
    assert payload["email"] == "test@example.com"
    assert payload["username"] == "testuser"
    assert payload["role"] == "user"
    assert payload["type"] == ACCESS_TOKEN_TYPE
    assert "jti" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_create_refresh_token(test_user):
    """Test that refresh token is created correctly."""
    token = create_refresh_token(test_user)

    assert token is not None
    assert isinstance(token, str)

    # Decode and verify payload
    payload = decode_token(token)
    assert payload["sub"] == "test-user-id"
    assert payload["type"] == REFRESH_TOKEN_TYPE
    assert "jti" in payload
    assert "exp" in payload


def test_decode_token_valid(test_user):
    """Test decoding a valid token."""
    token = create_access_token(test_user)
    payload = decode_token(token)

    assert payload["sub"] == "test-user-id"
    assert payload["email"] == "test@example.com"


def test_decode_token_invalid():
    """Test decoding an invalid token raises an error."""
    with pytest.raises(Exception):  # Should raise JWTError
        decode_token("invalid.token.here")


def test_get_token_payload(test_user):
    """Test getting payload without validation."""
    token = create_access_token(test_user)
    payload = get_token_payload(token)

    assert payload["sub"] == "test-user-id"
    assert payload["type"] == ACCESS_TOKEN_TYPE


def test_token_expiry(test_user):
    """Test that token has proper expiration."""
    import jwt
    from app.config import settings

    token = create_access_token(test_user)
    payload = decode_token(token)

    # Check that expiration is in the future
    exp = payload["exp"]
    now = datetime.now(timezone.utc).timestamp()

    assert exp > now
    assert exp <= now + (settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60) + 10


def test_refresh_token_expiry(test_user):
    """Test that refresh token has proper expiration."""
    import jwt
    from app.config import settings

    token = create_refresh_token(test_user)
    payload = decode_token(token)

    # Check that expiration is in the future (days)
    exp = payload["exp"]
    now = datetime.now(timezone.utc).timestamp()

    assert exp > now
    assert exp <= now + (settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60) + 10
