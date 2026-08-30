from datetime import datetime, timedelta, timezone

import pytest
import redis.exceptions

from features.auth.jwt import blacklist_token, is_token_blacklisted


@pytest.mark.asyncio
async def test_blacklist_token_marks_jti():
    try:
        from services.redis_service import RedisService
        redis = RedisService()
        await redis.connect()
        await redis.disconnect()
    except Exception:
        pytest.skip("Redis is not running in this environment; skipping token blacklist integration test.")

    jti = "test-jti-123"
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)

    await blacklist_token(jti, exp)

    assert await is_token_blacklisted(jti) is True


@pytest.mark.asyncio
async def test_blacklist_token_ignores_expired_token():
    try:
        from services.redis_service import RedisService
        redis = RedisService()
        await redis.connect()
        await redis.disconnect()
    except Exception:
        pytest.skip("Redis is not running in this environment; skipping token blacklist integration test.")

    jti = "expired-jti-456"
    exp = datetime.now(timezone.utc) - timedelta(minutes=1)

    await blacklist_token(jti, exp)

    assert await is_token_blacklisted(jti) is False
