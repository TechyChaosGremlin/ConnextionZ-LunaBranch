from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.storage import MediaStorage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(PROJECT_ROOT / "media")))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

MAX_AVATAR_BYTES = 8 * 1024 * 1024
MAX_MEDIA_BYTES = 512 * 1024 * 1024
AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MEDIA_TYPES = AVATAR_TYPES | {"video/mp4", "video/webm", "video/quicktime", "video/ogg"}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/ogg": ".ogv",
}
SIGNATURE_BYTES = 64 * 1024
media_storage = MediaStorage(MEDIA_ROOT)


def detect_media_type(header: bytes) -> str | None:
    """Return a supported MIME type based on file bytes, never request metadata."""
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    if header.startswith(b"\x1a\x45\xdf\xa3") and b"webm" in header:
        return "video/webm"
    if header.startswith(b"OggS") and b"theora" in header:
        return "video/ogg"
    if header[4:8] == b"ftyp":
        major_brand = header[8:12]
        if major_brand == b"qt  ":
            return "video/quicktime"
        if major_brand in {b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"M4V ", b"MSNV"}:
            return "video/mp4"
    return None


async def store_upload(upload: UploadFile, allowed_types: set[str], max_bytes: int) -> tuple[str, str]:
    temporary_file = MEDIA_ROOT / f".upload-{uuid.uuid4().hex}.tmp"
    size = 0
    header = bytearray()
    try:
        with temporary_file.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(status_code=413, detail="Uploaded file is too large")
                if len(header) < SIGNATURE_BYTES:
                    header.extend(chunk[:SIGNATURE_BYTES - len(header)])
                output.write(chunk)

        content_type = detect_media_type(bytes(header))
        if content_type is None or content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="Unsupported or invalid media file")

        filename = f"{uuid.uuid4().hex}{CONTENT_TYPE_EXTENSIONS[content_type]}"
        with temporary_file.open("rb") as source:
            url = media_storage.save(source, filename, content_type)
    except Exception:
        temporary_file.unlink(missing_ok=True)
        raise
    finally:
        temporary_file.unlink(missing_ok=True)
        await upload.close()
    return url, content_type