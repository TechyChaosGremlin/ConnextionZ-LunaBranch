# ConnextionZ Profile Backend

This backend is a minimal Python + GraphQL starter for profile data that matches the app contract in the profile screen.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For deployment, configure the session settings before starting the server:

```powershell
$env:ENVIRONMENT="production"
$env:SESSION_SECRET="replace-with-a-long-random-secret"
$env:SESSION_COOKIE_SECURE="true"
$env:SESSION_COOKIE_SAMESITE="lax"
$env:SESSION_MAX_AGE="604800"
```

Production startup refuses to run without `SESSION_SECRET`. Local development
uses a development-only fallback and keeps `SESSION_COOKIE_SECURE=false` so
sessions work over `http://localhost`.

Passwords are stored with bcrypt. Existing development accounts created before
bcrypt was enabled are upgraded automatically after their next successful login.

Uploaded avatars and post media are stored outside the database under `MEDIA_ROOT`
and served as URLs under `/media/`. Set `MEDIA_ROOT` to an object-storage mount
or replace `store_upload` with an S3-compatible client for deployment. The API
accepts authenticated multipart uploads at `/api/media/upload`. Each post-media
upload is recorded with its authenticated owner and returns `{ id, url,
contentType }`. Create posts with the owned `mediaId` and `thumbnailMediaId`;
the server resolves the URLs and does not accept client-supplied media URLs.

For AWS S3, set these variables and provide AWS credentials through the normal
AWS credential chain (environment variables, profile, or IAM role):

```powershell
$env:AWS_S3_BUCKET="connextionz-media-production"
$env:AWS_REGION="us-east-1"
$env:AWS_S3_PUBLIC_BASE_URL="https://cdn.example.com"
```

`AWS_S3_PUBLIC_BASE_URL` is optional; use a public S3 URL only for a bucket or
CDN path configured for public media delivery. For private buckets, replace the
returned URL with a CloudFront or signed-URL strategy before production use.

Production infrastructure also supports:

```powershell
$env:DATABASE_URL="postgresql+psycopg://user:password@host:5432/connextionz"
$env:CORS_ORIGINS="https://app.example.com"
$env:ALLOWED_HOSTS="api.example.com"
$env:REQUIRE_HTTPS="true"
```

The API applies a global `120/minute` per-IP limit, with stricter limits of
`10/minute` for login, `5/minute` for registration, and `30/minute` for media
uploads. `docker-compose.yml` provides a PostgreSQL 16 deployment template;
put TLS in the reverse proxy or load balancer in front of the API.

From the project root (the directory containing `alembic.ini`), database migrations are managed with Alembic:

```bash
python -m alembic current
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "describe the schema change"
```

Application startup runs `upgrade head` automatically. The existing `profiles.db`
is stamped with the initial revision on first startup so its data is preserved.

With the backend running on port `8002`, run the end-to-end API checks:

```powershell
python backend/test_api.py
```

The test creates a temporary account and verifies registration, login, own
profile queries, profile updates, logout, protected mutations, follow/unfollow,
and duplicate email/username rejection.

Then open:

- http://localhost:8000/graphql
- GraphQL playground / IDE will be available via the GraphQL route

## Main queries

```graphql
query Me {
  me {
    id
    username
    displayName
    bio
    avatarUrl
    followers
    following
    collabScore
    collabCount
  }
}

query Profile($username: String!) {
  profile(username: $username) {
    username
    displayName
    bio
    website
    location
    posts {
      id
      caption
      thumbnail
      likes
      views
    }
  }
}
```

## Main mutation

```graphql
mutation UpdateProfile {
  updateProfile(input: {
    bio: "I make cinematic short-form visuals"
    location: "Brooklyn"
    website: "example.com"
  }) {
    username
    bio
    location
    website
  }
}
```

Authenticated content operations are also available:

```graphql
query MyContent {
  myPosts { id thumbnail caption views likes collabWith }
  myPlaylists { id title cover itemLabel plays }
}

mutation CreatePost($input: PostInput!) {
  createPost(input: $input) { id thumbnail caption views likes collabWith }
}

# $input must include mediaId and thumbnailMediaId returned by /api/media/upload.
# Both records must belong to the authenticated user; thumbnailMediaId must be an image.

mutation CreatePlaylist($input: PlaylistInput!) {
  createPlaylist(input: $input) { id title cover itemLabel plays }
}
```

`updatePost`, `deletePost`, `updatePlaylist`, and `deletePlaylist` are owner-only
operations and require the authenticated session cookie.
