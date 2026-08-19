from fastapi import APIRouter, HTTPException, Request

from backend.app.auth import authenticate_user, get_user_profile, register_user


def create_auth_router(limiter) -> APIRouter:
    router = APIRouter()

    @router.post("/auth/login")
    @limiter.limit("10/minute")
    async def login(request: Request):
        """Log in and establish a session."""
        data = await request.json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        user = authenticate_user(email, password)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        request.session["user_id"] = user.id
        profile = get_user_profile(user.id)
        return {
            "ok": True,
            "user": {"id": user.id, "email": user.email},
            "profile": {
                "username": profile.username,
                "displayName": profile.display_name,
                "bio": profile.bio,
            } if profile else None,
        }

    @router.post("/auth/register")
    @limiter.limit("5/minute")
    async def register(request: Request):
        """Register an account and establish a session."""
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        username = data.get("username")
        display_name = data.get("display_name", username or "Creator")

        if not email or not password or not username:
            raise HTTPException(status_code=400, detail="Email, password, and username required")

        result = register_user(email, password, username, display_name)
        if result is None:
            raise HTTPException(status_code=409, detail="Email or username already registered, or profile data is invalid")

        user, profile = result
        request.session["user_id"] = user.id
        return {
            "ok": True,
            "user": {"id": user.id, "email": user.email},
            "profile": {
                "username": profile.username,
                "displayName": profile.display_name,
                "bio": profile.bio,
            },
        }

    @router.post("/auth/logout")
    async def logout(request: Request):
        """Log out by clearing the session."""
        request.session.clear()
        return {"ok": True}

    return router