from __future__ import annotations

import re
from urllib.parse import urlparse

USERNAME_RE = re.compile(r"[a-z0-9._]{3,24}")
DISPLAY_NAME_MAX = 40
BIO_MAX = 160


def normalize_username(value: str) -> str:
    return (value or "").strip().removeprefix("@").lower()


def validate_username(value: str) -> str:
    username = normalize_username(value)
    if not USERNAME_RE.fullmatch(username):
        raise ValueError("Usernames are 3-24 characters: letters, numbers, dots and underscores.")
    return username


def normalize_display_name(value: str) -> str:
    return " ".join((value or "").strip().split())


def validate_display_name(value: str) -> str:
    display_name = normalize_display_name(value)
    if not display_name:
        raise ValueError("Display name cannot be empty.")
    if len(display_name) > DISPLAY_NAME_MAX:
        raise ValueError("Display names can be up to 40 characters.")
    return display_name


def normalize_bio(value: str | None) -> str:
    return (value or "").strip()


def validate_bio(value: str | None) -> str:
    bio = normalize_bio(value)
    if len(bio) > BIO_MAX:
        raise ValueError("Bios can be up to 160 characters.")
    return bio


def normalize_website(value: str | None) -> str:
    website = (value or "").strip()
    if not website:
        return ""
    return website if re.match(r"^https?://", website, flags=re.IGNORECASE) else f"https://{website}"


def validate_website(value: str | None) -> str:
    website = normalize_website(value)
    if not website:
        return ""
    parsed = urlparse(website)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() not in {"http", "https"} or not host:
        raise ValueError("Enter a valid website URL, like https://example.com.")
    if "." not in host and host != "localhost":
        raise ValueError("Enter a valid website URL, like https://example.com.")
    return website


def normalize_avatar_url(value: str | None) -> str:
    return (value or "").strip()


def validate_avatar_url(value: str | None) -> str:
    avatar_url = normalize_avatar_url(value)
    if not avatar_url:
        return ""
    if avatar_url.startswith("data:"):
        return avatar_url
    parsed = urlparse(avatar_url)
    if parsed.scheme.lower() in {"http", "https"} and parsed.hostname:
        return avatar_url
    raise ValueError("Profile photos can only be uploaded from your device or kept as-is.")
