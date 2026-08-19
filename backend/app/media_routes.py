from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from backend.app.database import get_session
from backend.app.media import AVATAR_TYPES, MAX_AVATAR_BYTES, MAX_MEDIA_BYTES, MEDIA_TYPES, store_upload
from backend.app.models import Media


def create_media_router(limiter) -> APIRouter:
    router = APIRouter()

    @router.post("/api/avatar/upload")
    @limiter.limit("30/minute")
    async def upload_avatar(request: Request, file: UploadFile = File(...)):
        if request.session.get("user_id") is None:
            raise HTTPException(status_code=401, detail="Must be logged in to upload an avatar")
        url, content_type = await store_upload(file, AVATAR_TYPES, MAX_AVATAR_BYTES)
        return {"ok": True, "url": url, "contentType": content_type}

    @router.post("/api/media/upload")
    @limiter.limit("30/minute")
    async def upload_media(request: Request, file: UploadFile = File(...)):
        user_id = request.session.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Must be logged in to upload media")
        url, content_type = await store_upload(file, MEDIA_TYPES, MAX_MEDIA_BYTES)
        with get_session() as session:
            media = Media(user_id=user_id, url=url, content_type=content_type)
            session.add(media)
            session.commit()
            session.refresh(media)
        return {"ok": True, "id": str(media.id), "url": url, "contentType": content_type}

    return router