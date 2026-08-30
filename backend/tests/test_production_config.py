import pytest

from app.config import Settings


def test_production_rejects_debug_mode():
    with pytest.raises(ValueError, match="DEBUG.*production"):
        Settings(
            environment="production",
            debug=True,
            jwt_secret_key="a-very-long-production-secret-that-is-safe-123",
        )


def test_production_requires_secure_jwt_secret():
    with pytest.raises(ValueError, match="JWT_SECRET_KEY.*secure"):
        Settings(
            environment="production",
            debug=False,
            jwt_secret_key="change-me-in-production-32-bytes-minimum",
        )
