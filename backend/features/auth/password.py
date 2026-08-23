"""
Password hashing and validation utilities.

Uses bcrypt via passlib for secure password hashing.
Implements password strength validation.
"""

from __future__ import annotations

import re
from typing import Any

from passlib.context import CryptContext
from passlib.exc import PasswordValueError

# Password hashing context
# Uses bcrypt for secure hashing with automatic salt generation
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Adjust based on security requirements
)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password.

    Args:
        password: The plain-text password to hash

    Returns:
        The hashed password string

    Raises:
        PasswordValueError: If password is too weak or invalid
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hash.

    Args:
        plain_password: The plain-text password to verify
        hashed_password: The hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def check_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Check if a password meets strength requirements.

    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character

    Args:
        password: The password to check

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    # Uppercase check
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    # Lowercase check
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    # Digit check
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")

    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def validate_password(password: str) -> None:
    """
    Validate password strength and raise exception if invalid.

    Args:
        password: The password to validate

    Raises:
        PasswordValueError: If password doesn't meet strength requirements
    """
    is_valid, errors = check_password_strength(password)
    if not is_valid:
        raise PasswordValueError(
            "Password does not meet strength requirements: " + "; ".join(errors)
        )


# Common password list (subset - in production, use a more comprehensive list)
COMMON_PASSWORDS = {
    "password",
    "password123",
    "123456",
    "123456789",
    "qwerty",
    "abc123",
    "monkey",
    "master",
    "dragon",
    "login",
    "princess",
    "football",
    "shadow",
    "sunshine",
    "trustno1",
    "iloveyou",
    "batman",
    "access",
    "hello",
    "charlie",
    "donald",
    "password1",
    "qwerty123",
}


def is_common_password(password: str) -> bool:
    """
    Check if password is a commonly used password.

    Args:
        password: The password to check

    Returns:
        True if password is common, False otherwise
    """
    return password.lower() in COMMON_PASSWORDS


def validate_password_not_common(password: str) -> None:
    """
    Validate that password is not a common password.

    Args:
        password: The password to validate

    Raises:
        PasswordValueError: If password is a common password
    """
    if is_common_password(password):
        raise PasswordValueError(
            "Password is too common. Please choose a more unique password."
        )
