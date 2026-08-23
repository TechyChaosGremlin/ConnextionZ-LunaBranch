"""
Test script to verify auth system fixes.
Run with: python test_auth_fixes.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all auth modules can be imported."""
    print("Testing imports...")
    
    try:
        from features.auth.jwt import create_access_token, decode_token
        print("  ✓ features.auth.jwt")
    except Exception as e:
        print(f"  ✗ features.auth.jwt: {e}")
        return False
    
    try:
        from features.auth.rbac import require_role, has_permission
        print("  ✓ features.auth.rbac")
    except Exception as e:
        print(f"  ✗ features.auth.rbac: {e}")
        return False
    
    try:
        from features.auth.middleware import get_current_user
        print("  ✓ features.auth.middleware")
    except Exception as e:
        print(f"  ✗ features.auth.middleware: {e}")
        return False
    
    try:
        from features.auth.password import hash_password, verify_password
        print("  ✓ features.auth.password")
    except Exception as e:
        print(f"  ✗ features.auth.password: {e}")
        return False
    
    try:
        from services.redis_service import RedisService
        print("  ✓ services.redis_service")
    except Exception as e:
        print(f"  ✗ services.redis_service: {e}")
        return False
    
    return True

def test_jwt_creation():
    """Test JWT token creation with mock user."""
    print("\nTesting JWT creation...")
    
    try:
        from app.models.user import User, UserRole
        from features.auth.jwt import create_access_token, decode_token
        
        # Create a mock user (without DB)
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        
        # Create token
        token = create_access_token(user)
        print(f"  ✓ Token created: {token[:20]}...")
        
        # Decode token
        payload = decode_token(token)
        print(f"  ✓ Token decoded, user_id: {payload.get('sub')}")
        
        return True
    except Exception as e:
        print(f"  ✗ JWT creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Auth System Fix Verification")
    print("=" * 60)
    
    imports_ok = test_imports()
    
    if imports_ok:
        jwt_ok = test_jwt_creation()
    else:
        jwt_ok = False
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if imports_ok and jwt_ok:
        print("✓ All tests passed! Auth system is working.")
        sys.exit(0)
    else:
        print("✗ Some tests failed.")
        sys.exit(1)
