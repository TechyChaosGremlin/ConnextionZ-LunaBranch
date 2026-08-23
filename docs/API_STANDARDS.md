# ============================================================================
# ConnextionZ Platform — API Standards
# ============================================================================
#
# This document defines the API standards and conventions for the ConnextionZ
# platform. All developers (frontend and backend) must adhere to these standards
# when building or consuming APIs.
#
# ============================================================================

## 1. API Protocols

| Protocol | Use Case | Notes |
|----------|----------|-------|
| **GraphQL** | Primary data-fetching protocol for web and mobile clients | Served at `POST /api/graphql`; GraphiQL at `GET /api/graphql` |
| **REST** | Auth endpoints, webhooks, health checks, OAuth callbacks | Served at well-known paths (`/auth/*`, `/health`, etc.) |
| **WebSocket** | Real-time features: messaging, notifications, live streaming | Socket.IO for web; native WebSocket for mobile |
| **GraphQL Subscriptions** | Real-time feed updates, collaboration status changes | GraphQL-WS protocol via Strawberry |

## 2. GraphQL Conventions

### 2.1 Request Format

All GraphQL requests use the standard POST method with `application/json` content type:

```json
{
  "query": "query GetFeed($first: Int!, $after: String) { feed(first: $first, after: $after) { edges { node { id title } } pageInfo { hasNextPage } } }",
  "variables": { "first": 20, "after": null },
  "operationName": "GetFeed"
}
```

### 2.2 Error Format

All GraphQL errors follow the GraphQL spec with a consistent `extensions` shape:

```json
{
  "errors": [
    {
      "message": "User not found",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["profile"],
      "extensions": {
        "code": "NOT_FOUND",
        "statusCode": 404,
        "requestId": "req_abc123"
      }
    }
  ]
}
```

**Standard error codes:**

| Code | HTTP Status | Meaning |
|------|------------|---------|
| `UNAUTHENTICATED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Insufficient permissions (RBAC) |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `CONFLICT` | 409 | Resource already exists (e.g., duplicate email) |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### 2.3 Pagination (Relay Connection Spec)

All list queries use cursor-based pagination following the Relay Connection specification:

```graphql
type SomeConnection {
  edges: [SomeEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type SomeEdge {
  cursor: String!
  node: SomeType!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

**Query parameters:**
- `first: Int` — Number of items to return (default: 20, max: 100)
- `after: String` — Opaque cursor for the next page

Cursors are base64-encoded representations of the item's sort key (typically `created_at` timestamp + `id`).

### 2.4 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Query fields | `camelCase` | `creatorAnalytics`, `unreadNotificationCount` |
| Mutation fields | `camelCase` | `createPost`, `sendMessage` |
| Types | `PascalCase` | `User`, `CollaborationParticipant` |
| Input types | `PascalCase` + `Input` suffix | `RegisterInput`, `CreatePostInput` |
| Enum values | `SCREAMING_SNAKE_CASE` | `IN_PROGRESS`, `COLLABORATION_INVITE` |
| Connection types | `PascalCase` + `Connection` suffix | `PostConnection` |

## 3. REST Conventions

### 3.1 URL Structure

```
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{sub-resource}
```

**Examples:**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users/{id}`
- `GET /health`

### 3.2 Response Envelope

**Success (single resource):**
```json
{
  "data": { "id": "...", "email": "..." }
}
```

**Success (list):**
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "perPage": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

**Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password too weak",
    "details": {
      "errors": ["Must contain at least one uppercase letter"]
    }
  }
}
```

### 3.3 HTTP Methods

| Method | Usage |
|--------|-------|
| `GET` | Read resource(s) |
| `POST` | Create resource |
| `PUT` | Full update |
| `PATCH` | Partial update |
| `DELETE` | Delete (soft-delete via `PATCH` in most cases) |

## 4. Authentication

### 4.1 Token Format

All authenticated requests must include a JWT in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### 4.2 Token Lifecycle

| Token | TTL | Rotation |
|-------|-----|----------|
| Access Token | 15 minutes | Rotated on refresh |
| Refresh Token | 7 days | Rotated on each use |

### 4.3 GraphQL Auth

GraphQL queries/mutations use the same `Authorization: Bearer <token>` header.
The auth middleware extracts the user before the resolver runs.

**Public queries (no auth required):**
- Trending sounds, creator discovery, public profiles

**Authenticated queries:**
- Everything else — enforced via `Permissions` in resolvers.

## 5. Rate Limiting

| Tier | Limit | Window |
|------|-------|--------|
| Unauthenticated | 30 requests | 60 seconds |
| Authenticated (User) | 100 requests | 60 seconds |
| Authenticated (Creator) | 300 requests | 60 seconds |
| Authenticated (Admin) | 1000 requests | 60 seconds |

Rate limit headers in REST responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1690000000
```

GraphQL rate limiting counts by query complexity (cost model TBD).

## 6. Timestamps

- All timestamps use **ISO 8601 UTC** format: `2026-07-08T19:00:00Z`
- Timestamps are always in UTC (no local timezone offsets)
- Database columns use `TIMESTAMPTZ`
- API responses use string serialization

## 7. IDs

- All primary keys are **UUID v7** (time-sortable)
- IDs are serialized as lowercase UUID strings in API responses
- Example: `"0190-acbd-7e00-0000-8f3a2b1c4d5e"`

## 8. CORS

Allowed origins are configured via `ALLOWED_ORIGINS` environment variable:

| Environment | Origins |
|-------------|---------|
| Development | `http://localhost:3000`, `http://localhost:19006` (React Native) |
| Staging | `https://staging.connextionz.com` |
| Production | `https://connextionz.com`, `capacitor://localhost`, `ionic://localhost` |

## 9. Versioning

- **GraphQL:** No versioning — the schema is the contract; deprecated fields are marked `@deprecated`
- **REST:** URL-based versioning (`/api/v1/`, `/api/v2/`)
- Breaking changes trigger a major version bump

## 10. Caching

| Layer | TTL | Strategy |
|-------|-----|----------|
| CDN (CloudFront) | 1 hour | Cache-Control: public, max-age=3600 for static assets |
| API Cache (Redis) | 5 minutes | Cache based on query hash; invalidated on mutation |
| Client Cache (Apollo) | Configurable | Normalized cache with field-level policies |

Cache-Control headers for REST:
```
Cache-Control: private, max-age=300
```

## 11. WebSocket / Subscriptions

### 11.1 Connection

```
ws://localhost:8000/api/graphql  (WebSocket for GraphQL subscriptions)
wss://api.connextionz.com/api/graphql  (Production)
```

### 11.2 Authentication

WebSocket connections pass the JWT as a connection parameter:
```json
{
  "connectionParams": {
    "Authorization": "Bearer <access_token>"
  }
}
```

### 11.3 Subscription Protocol

Uses `graphql-ws` protocol (not `subscriptions-transport-ws`).

## 12. File Uploads

File uploads use **pre-signed S3 URLs**:
1. Client requests an upload URL via `getUploadUrl` query
2. Client uploads directly to S3 via the pre-signed URL
3. Client submits the S3 key with the GraphQL mutation

This avoids streaming large files through the API server.

## 13. Health Checks

| Endpoint | Purpose | Kubernetes Probe |
|----------|---------|-----------------|
| `GET /health` | Basic liveness | `livenessProbe` |
| `GET /health/ready` | Dependency readiness (DB, Redis, MQ) | `readinessProbe` |
| `GET /health/live` | Application alive | `livenessProbe` |

## 14. Content Security & Input Validation

- All GraphQL inputs are validated by Strawberry type system
- String fields have length limits enforced at the resolver level
- File uploads have size limits (10 MB default for images, 500 MB for video)
- User-generated HTML is sanitized before storage
- SQL injection is prevented by SQLAlchemy parameterized queries
