# Auth Integration Complete

## Backend (Python + FastAPI + Strawberry GraphQL)

### Auth Endpoints
- **POST /auth/login** — Session-based login with email/password
- **POST /auth/register** — Create new account with profile
- **POST /auth/logout** — Clear session cookie

### GraphQL Resolvers
- **Query.me** — Returns logged-in user's profile (requires valid session)
- **Query.profile(username)** — Public profile lookup by username
- **Mutation.updateProfile** — Update own profile (requires auth + session validation)

### Session Management
- Uses FastAPI SessionMiddleware with httpOnly cookies
- Secret key in `backend/app/main.py` (change in production)
- Session context passed to GraphQL via `info.context["user_id"]`

### Database Models
- `User` — Email + password_hash + timestamps
- `Profile` — All public profile fields linked to User
- `Post` — Posts with thumbnails, captions, views/likes
- `Playlist` — Collections with covers and play counts
- `Follow` — Follower relationships (ready to wire)

### Seeded User
Email: `demo@connextionz.app`
Password: `demo`
Profile: Luna Hart with 2 posts and 2 playlists

---

## Frontend (React + TypeScript)

### Configuration
- Backend URL: `http://127.0.0.1:8002` (configurable via `REACT_APP_API_URL`)
- GraphQL endpoint: `/graphql` on backend
- Auth fallback: Uses localStorage demo auth if backend unavailable

### Auth Flow
1. Login form calls `signIn()` → tries backend, falls back to demo
2. Backend returns session cookie (httpOnly)
3. Frontend stores minimal user data in Account object
4. All GraphQL requests include credentials (cookies)
5. Backend validates session and returns user-specific data

### Modified Files
- [src/app/api-config.ts](src/app/api-config.ts) — Backend URL configuration
- [src/app/auth-store.ts](src/app/auth-store.ts) — Backend integration + fallback
- [src/app/profile-graphql.ts](src/app/profile-graphql.ts) — Credentials + backend endpoint

---

## Next Steps

### Immediate
1. Test login → GraphQL query flow end-to-end
2. Verify profile updates persist to database
3. Test logout clears session

### Short-term
1. **Follows API** — Count follower/following from database
2. **Posts/Playlists** — Serve from database instead of static fixtures
3. **Avatar uploads** — Store files and persist URLs

### Medium-term
1. Real password hashing (argon2 or bcrypt, not plaintext)
2. JWT tokens for stateless auth or refresh token flow
3. Email verification for new accounts
4. Password reset flow with email links
5. OAuth integration (Google, Apple)

---

## Debugging

**Backend won't start:**
```ps1
cd c:\Users\natur\OneDrive\Documents\GitHub\ConnextionZ-frontend
& "C:/Users/natur/AppData/Local/Programs/Python/Python314/python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002 --reload
```

**Check imports:**
```ps1
& "C:/Users/natur/AppData/Local/Programs/Python/Python314/python.exe" -c "from backend.app.main import app; print('OK')"
```

**Test login:**
```ps1
cd backend; & "C:/Users/natur/AppData/Local/Programs/Python/Python314/python.exe" test_auth.py
```

**Database:**
SQLite at `./profiles.db` — delete to reset seeded data
