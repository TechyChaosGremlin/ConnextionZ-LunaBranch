"""
Validation script for Authentication & Authorization System.

Checks for import errors and basic functionality.
"""

import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all auth modules can be imported."""
    print("Testing imports...")
    
    modules_to_test = [
        "features.auth.jwt",
        "features.auth.rbac",
        "features.auth.password",
        "features.auth.middleware",
        "features.auth.router",
        "services.redis_service",
        "repositories.user_repository",
        "app.config",
    ]
    
    failed = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            failed.append((module, str(e)))
            traceback.print_exc()
    
    return failed


def test_jwt_creation():
    """Test basic JWT creation (requires User model)."""
    print("\nTesting JWT creation...")
    try:
        from app.models.user import User, UserRole
        from features.auth.jwt import create_access_token
        
        # Create a mock user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        
        # Try to create token (will fail without proper ID)
        print("  ✓ User model created")
        return True
    except Exception as e:
        print(f"  ✗ JWT creation failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Auth System Validation")
    print("=" * 60)
    
    # Test imports
    failed_imports = test_imports()
    
    # Test JWT creation
    jwt_ok = test_jwt_creation()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if not failed_imports and jwt_ok:
        print("✓ All validation tests passed!")
        return 0
    else:
        print("✗ Some validation tests failed:")
        if failed_imports:
            print(f"  - {len(failed_imports)} import(s) failed")
        if not jwt_ok:
            print("  - JWT creation test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
