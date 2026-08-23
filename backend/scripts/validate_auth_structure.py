"""
Simple validation script for Authentication & Authorization System.

Checks file structure and basic Python syntax without importing modules.
"""

import ast
import sys
from pathlib import Path

def check_file_syntax(filepath: Path) -> tuple[bool, str]:
    """
    Check if a Python file has valid syntax.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def validate_auth_system():
    """Validate the auth system file structure and syntax."""
    print("=" * 60)
    print("Auth System Structure Validation")
    print("=" * 60)
    
    # Define expected files
    project_root = Path(__file__).parent.parent
    files_to_check = [
        # Auth module
        project_root / "features" / "auth" / "__init__.py",
        project_root / "features" / "auth" / "jwt.py",
        project_root / "features" / "auth" / "rbac.py",
        project_root / "features" / "auth" / "middleware.py",
        project_root / "features" / "auth" / "password.py",
        project_root / "features" / "auth" / "router.py",
        
        # Services
        project_root / "services" / "redis_service.py",
        
        # Repositories
        project_root / "repositories" / "user_repository.py",
        
        # App core
        project_root / "app" / "main.py",
        project_root / "app" / "config.py",
        project_root / "app" / "dependencies.py",
        project_root / "app" / "db" / "session.py",
        
        # Tests
        project_root / "tests" / "test_auth_jwt.py",
    ]
    
    print("\nChecking file existence and syntax...")
    
    all_valid = True
    for filepath in files_to_check:
        if not filepath.exists():
            print(f"  ✗ {filepath.relative_to(project_root)} - FILE NOT FOUND")
            all_valid = False
            continue
        
        is_valid, error = check_file_syntax(filepath)
        if is_valid:
            print(f"  ✓ {filepath.relative_to(project_root)}")
        else:
            print(f"  ✗ {filepath.relative_to(project_root)} - SYNTAX ERROR: {error}")
            all_valid = False
    
    # Check for __init__.py files
    print("\nChecking package structure...")
    packages = [
        project_root / "features",
        project_root / "features" / "auth",
        project_root / "services",
        project_root / "repositories",
        project_root / "app",
        project_root / "app" / "db",
        project_root / "tests",
    ]
    
    for pkg in packages:
        init_file = pkg / "__init__.py"
        if init_file.exists():
            print(f"  ✓ {pkg.relative_to(project_root)}/")
        else:
            print(f"  ✗ {pkg.relative_to(project_root)}/ - MISSING __init__.py")
            all_valid = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if all_valid:
        print("✓ All files exist and have valid Python syntax!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r app/requirements.txt")
        print("  2. Set up PostgreSQL database")
        print("  3. Set up Redis instance")
        print("  4. Run unit tests: pytest tests/test_auth_jwt.py")
        print("  5. Start the API server: uvicorn app.main:app --reload")
        return 0
    else:
        print("✗ Some files are missing or have syntax errors")
        return 1


if __name__ == "__main__":
    sys.exit(validate_auth_system())
