"""
GraphQL schema and resolvers using Strawberry (code-first).

Exposes a single :func:`create_graphql_router` factory that wires
all types, queries, mutations, and subscriptions into a FastAPI-compatible
router via ``strawberry.fastapi.GraphQLRouter``.

Auth is enforced per-resolver via ``AppContext`` which carries the
DB session and optional authenticated ``User`` ORM instance extracted
from the JWT Bearer token.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Callable

import strawberry
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.types import Info as StrawberryInfo

from app.models.user import User
from app.config import settings

# ── Custom Scalars ───────────────────────────────────────────────────────────

UUIDScalar = strawberry.scalar(
    uuid.UUID,
    serialize=lambda v: str(v),
    parse_value=lambda v: uuid.UUID(v) if isinstance(v, str) else v,
    description="UUID v7 identifier",
)

DateTimeScalar = strawberry.scalar(
    datetime,
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
    description="ISO 8601 UTC datetime",
)

JSONScalar = strawberry.scalar(
    object,
    serialize=lambda v: v,
    parse_value=lambda v: v,
    description="Arbitrary JSON object",
)


# ── GraphQL Errors ───────────────────────────────────────────────────────────


@strawberry.type
class GraphQLError:
    """Structured error returned alongside partial data in mutations/queries."""

    message: str
    code: str
    field: Optional[str] = None


# ── Context ──────────────────────────────────────────────────────────────────


class AppContext(BaseContext):
    """GraphQL context carrying DB session and authenticated user.

    Populated by the ``context_getter`` factory before every resolver execution.
    The DB session is obtained from the FastAPI session factory dependency.
    If the request includes a valid ``Authorization: Bearer <jwt>`` header,
    the corresponding ``User`` ORM instance is loaded and stored.
    """

    def __init__(self, db: AsyncSession, current_user: User | None = None) -> None:
        self.db: AsyncSession = db
        self._current_user: User | None = current_user

    @property
    def current_user(self) -> User | None:
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def require_auth(self) -> User:
        """Return the authenticated user or raise a ``PermissionError``."""
        if self._current_user is None:
            raise PermissionError("Authentication required")
        return self._current_user


# ── Enums ────────────────────────────────────────────────────────────────────


@strawberry.enum
class UserRole:
    ADMIN = "admin"
    CREATOR = "creator"
    USER = "user"
    GUEST = "guest"


@strawberry.enum
class AccountStatus:
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING_VERIFICATION = "pending_verification"


@strawberry.enum
class ContentType:
    POST = "post"
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    LIVE_STREAM = "live_stream"


@strawberry.enum
class ContentStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FLAGGED = "flagged"
    REMOVED = "removed"


@strawberry.enum
class CollaborationStatus:
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@strawberry.enum
class MilestoneStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISPUTED = "disputed"


@strawberry.enum
class NotificationType:
    COLLABORATION_INVITE = "collaboration_invite"
    COLLABORATION_ACCEPTED = "collaboration_accepted"
    COLLABORATION_COMPLETED = "collaboration_completed"
    NEW_FOLLOWER = "new_follower"
    NEW_COMMENT = "new_comment"
    NEW_LIKE = "new_like"
    MENTION = "mention"
    MESSAGE = "message"
    BADGE_EARNED = "badge_earned"
    ENDORSEMENT_RECEIVED = "endorsement_received"
    MILESTONE_COMPLETED = "milestone_completed"
    SYSTEM = "system"


@strawberry.enum
class NotificationChannel:
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"


@strawberry.enum
class ReportTargetType:
    POST = "post"
    COMMENT = "comment"
    USER = "user"
    MESSAGE = "message"


@strawberry.enum
class ReportStatus:
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@strawberry.enum
class SortDirection:
    ASC = "ASC"
    DESC = "DESC"


@strawberry.enum
class FeedAlgorithm:
    PERSONALIZED = "PERSONALIZED"
    TRENDING = "TRENDING"
    RECENT = "RECENT"
    FOLLOWING = "FOLLOWING"


# ── Pagination Types (Relay Connection Spec) ──────────────────────────────────


@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None


# ── Core Types ───────────────────────────────────────────────────────────────


@strawberry.type
class UserType:
    id: UUIDScalar
    email: str
    username: str
    role: UserRole
    status: AccountStatus
    email_verified: bool
    mfa_enabled: bool
    last_login_at: Optional[DateTimeScalar] = None
    created_at: DateTimeScalar
    updated_at: DateTimeScalar

    @strawberry.field
    async def profile(self, info: StrawberryInfo[AppContext, None]) -> Optional["ProfileType"]:
        """Lazy-load profile via dataloader (placeholder)."""
        return None  # TODO: implement dataloader


@strawberry.type
class ProfileType:
    id: UUIDScalar
    user_id: UUIDScalar
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    social_links: Optional[JSONScalar] = None
    tags: Optional[List[str]] = None

    follower_count: int = 0
    following_count: int = 0
    collaboration_count: int = 0
    total_likes: int = 0

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class PostType:
    id: UUIDScalar
    user_id: UUIDScalar
    content_type: ContentType
    status: ContentStatus
    title: Optional[str] = None
    body: Optional[str] = None
    caption: Optional[str] = None
    tags: Optional[List[str]] = None
    mentions: Optional[List[UUIDScalar]] = None
    sound_track: Optional[str] = None

    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0

    scheduled_at: Optional[DateTimeScalar] = None
    published_at: Optional[DateTimeScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class MediaType:
    id: UUIDScalar
    post_id: UUIDScalar
    user_id: UUIDScalar
    media_type: str
    url: str
    thumbnail_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    is_processed: bool = False

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class CommentType:
    id: UUIDScalar
    post_id: UUIDScalar
    user_id: UUIDScalar
    parent_id: Optional[UUIDScalar] = None
    body: str
    is_edited: bool = False
    like_count: int = 0

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


# ── Collaboration Types ──────────────────────────────────────────────────────


@strawberry.type
class CollaborationType:
    id: UUIDScalar
    initiator_id: UUIDScalar
    title: str
    description: Optional[str] = None
    status: CollaborationStatus
    content_type: Optional[str] = None
    platform: Optional[str] = None
    tags: Optional[List[str]] = None

    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_currency: str = "USD"

    proposed_at: Optional[DateTimeScalar] = None
    started_at: Optional[DateTimeScalar] = None
    completed_at: Optional[DateTimeScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class CollaborationParticipantType:
    id: UUIDScalar
    collaboration_id: UUIDScalar
    user_id: UUIDScalar
    role: str
    accepted: bool = False
    accepted_at: Optional[DateTimeScalar] = None


@strawberry.type
class MilestoneType:
    id: UUIDScalar
    collaboration_id: UUIDScalar
    title: str
    description: Optional[str] = None
    status: MilestoneStatus
    sort_order: int = 0
    due_at: Optional[DateTimeScalar] = None
    completed_at: Optional[DateTimeScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


# ── Messaging Types ──────────────────────────────────────────────────────────


@strawberry.type
class ConversationType:
    id: UUIDScalar
    title: Optional[str] = None
    is_group: bool = False

    last_message_text: Optional[str] = None
    last_message_at: Optional[DateTimeScalar] = None
    last_message_by: Optional[UUIDScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class ConversationParticipantInfoType:
    id: UUIDScalar
    conversation_id: UUIDScalar
    user_id: UUIDScalar
    is_admin: bool = False
    last_read_at: Optional[DateTimeScalar] = None
    is_muted: bool = False


@strawberry.type
class MessageType:
    id: UUIDScalar
    conversation_id: UUIDScalar
    sender_id: UUIDScalar
    body: str
    content_type: str = "text"
    attachments: Optional[JSONScalar] = None
    is_edited: bool = False
    edited_at: Optional[DateTimeScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


# ── Notification Types ───────────────────────────────────────────────────────


@strawberry.type
class NotificationTypeDef:
    id: UUIDScalar
    user_id: UUIDScalar
    type: NotificationType
    title: str
    body: Optional[str] = None
    data: Optional[JSONScalar] = None
    channel: NotificationChannel
    is_read: bool = False
    read_at: Optional[DateTimeScalar] = None
    actor_id: Optional[UUIDScalar] = None

    created_at: DateTimeScalar


# ── Reputation Types ─────────────────────────────────────────────────────────


@strawberry.type
class ReputationScoreType:
    id: UUIDScalar
    user_id: UUIDScalar
    overall_score: float = 0.0
    collaboration_score: float = 0.0
    content_quality_score: float = 0.0
    community_score: float = 0.0
    reliability_score: float = 0.0
    total_endorsements: int = 0
    completed_collaborations: int = 0
    on_time_delivery_rate: float = 0.0
    computed_at: Optional[DateTimeScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class EndorsementType:
    id: UUIDScalar
    endorser_id: UUIDScalar
    endorsee_id: UUIDScalar
    category: str
    comment: Optional[str] = None
    rating: int
    collaboration_id: Optional[UUIDScalar] = None

    created_at: DateTimeScalar


@strawberry.type
class BadgeType:
    id: UUIDScalar
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    category: str
    tier: int = 1

    created_at: DateTimeScalar


@strawberry.type
class UserBadgeType:
    id: UUIDScalar
    user_id: UUIDScalar
    badge_id: UUIDScalar

    awarded_at: Optional[DateTimeScalar] = None
    awarded_by: Optional[UUIDScalar] = None


# ── Live Streaming ───────────────────────────────────────────────────────────


@strawberry.type
class LiveStreamType:
    id: UUIDScalar
    user_id: UUIDScalar
    title: str
    status: ContentStatus
    stream_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    viewer_count: int = 0
    started_at: Optional[DateTimeScalar] = None
    ended_at: Optional[DateTimeScalar] = None

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


# ── Sound ────────────────────────────────────────────────────────────────────


@strawberry.type
class SoundType:
    id: UUIDScalar
    name: str
    artist: Optional[str] = None
    source_url: Optional[str] = None
    cover_url: Optional[str] = None
    usage_count: int = 0
    trending_score: float = 0.0


# ── Creator Discovery ────────────────────────────────────────────────────────


@strawberry.type
class CreatorCardType:
    user: UserType
    profile: ProfileType
    relevance_score: float
    matching_tags: Optional[List[str]] = None
    reputation_score: Optional[float] = None


# ── Brand Partnerships ───────────────────────────────────────────────────────


@strawberry.type
class BrandOpportunityType:
    id: UUIDScalar
    brand_id: UUIDScalar
    title: str
    description: Optional[str] = None
    requirements: Optional[JSONScalar] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_currency: str = "USD"
    deadline: Optional[DateTimeScalar] = None
    status: CollaborationStatus

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class BrandApplicationType:
    id: UUIDScalar
    opportunity_id: UUIDScalar
    creator_id: UUIDScalar
    message: Optional[str] = None
    status: CollaborationStatus

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


# ── Search ───────────────────────────────────────────────────────────────────


@strawberry.type
class SearchResultType:
    type: str
    score: float
    user: Optional[UserType] = None
    post: Optional[PostType] = None
    sound: Optional[SoundType] = None
    collaboration: Optional[CollaborationType] = None


# ── Trust & Safety ───────────────────────────────────────────────────────────


@strawberry.type
class ReportType:
    id: UUIDScalar
    reporter_id: UUIDScalar
    target_type: ReportTargetType
    target_id: UUIDScalar
    reason: str
    description: Optional[str] = None
    status: ReportStatus

    created_at: DateTimeScalar
    updated_at: DateTimeScalar


# ── Analytics ────────────────────────────────────────────────────────────────


@strawberry.type
class PostAnalyticsType:
    post: PostType
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    avg_watch_time: Optional[float] = None
    completion_rate: Optional[float] = None


@strawberry.type
class AnalyticsSummaryType:
    period_start: DateTimeScalar
    period_end: DateTimeScalar

    total_posts: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0

    follower_growth: int = 0
    new_followers: int = 0
    lost_followers: int = 0

    active_collaborations: int = 0
    completed_collaborations: int = 0
    total_earnings: Optional[float] = None
    earnings_currency: str = "USD"

    engagement_rate: float = 0.0

    top_posts: Optional[List[PostAnalyticsType]] = None


# ── Auth Payload ─────────────────────────────────────────────────────────────


@strawberry.type
class AuthPayloadType:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserType


# ── Connection Types ─────────────────────────────────────────────────────────

# (Placeholder — full connection types will use generic edge/node patterns)


@strawberry.type
class PostEdge:
    cursor: str
    node: PostType


@strawberry.type
class PostConnection:
    edges: List[PostEdge]
    page_info: PageInfo
    total_count: int


# ── Input Types ──────────────────────────────────────────────────────────────


@strawberry.input
class RegisterInput:
    email: str
    username: str
    password: str


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.input
class RefreshTokenInput:
    refresh_token: str


@strawberry.input
class UpdateProfileInput:
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    social_links: strawberry.scalars.JSON | None = None
    tags: Optional[List[str]] = None


@strawberry.input
class CreatePostInput:
    content_type: ContentType
    title: Optional[str] = None
    body: Optional[str] = None
    caption: Optional[str] = None
    tags: Optional[List[str]] = None
    sound_track: Optional[str] = None
    scheduled_at: Optional[DateTimeScalar] = None
    media_urls: Optional[List[str]] = None


@strawberry.input
class FeedFilter:
    algorithm: Optional[FeedAlgorithm] = None
    content_type: Optional[ContentType] = None
    tags: Optional[List[str]] = None


@strawberry.input
class SearchInput:
    query: str
    types: Optional[List[str]] = None


@strawberry.input
class AnalyticsPeriod:
    start: DateTimeScalar
    end: DateTimeScalar


@strawberry.input
class CreateCommentInput:
    post_id: UUIDScalar
    parent_id: Optional[UUIDScalar] = None
    body: str


@strawberry.input
class CreateCollaborationInput:
    title: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    platform: Optional[str] = None
    tags: Optional[List[str]] = None
    participant_ids: List[UUIDScalar]
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_currency: Optional[str] = None


@strawberry.input
class CreateConversationInput:
    participant_ids: List[UUIDScalar]
    title: Optional[str] = None
    initial_message: Optional[str] = None


@strawberry.input
class SendMessageInput:
    conversation_id: UUIDScalar
    body: str
    content_type: Optional[str] = None
    attachments: Optional[JSONScalar] = None


@strawberry.input
class CreateBrandOpportunityInput:
    title: str
    description: Optional[str] = None
    requirements: Optional[JSONScalar] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_currency: Optional[str] = None
    deadline: Optional[DateTimeScalar] = None


@strawberry.input
class ApplyToBrandInput:
    opportunity_id: UUIDScalar
    message: Optional[str] = None


@strawberry.input
class EndorseUserInput:
    endorsee_id: UUIDScalar
    category: str
    comment: Optional[str] = None
    rating: int
    collaboration_id: Optional[UUIDScalar] = None


@strawberry.input
class ReportContentInput:
    target_type: ReportTargetType
    target_id: UUIDScalar
    reason: str
    description: Optional[str] = None


# ── Connection Types ─────────────────────────────────────────────────────────


@strawberry.type
class PostEdge:
    cursor: str
    node: PostType


@strawberry.type
class PostConnection:
    edges: List[PostEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class CollaborationEdge:
    cursor: str
    node: CollaborationType


@strawberry.type
class CollaborationConnection:
    edges: List[CollaborationEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class MessageEdge:
    cursor: str
    node: MessageType


@strawberry.type
class MessageConnection:
    edges: List[MessageEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class ConversationEdge:
    cursor: str
    node: ConversationType


@strawberry.type
class ConversationConnection:
    edges: List[ConversationEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class NotificationEdge:
    cursor: str
    node: NotificationTypeDef


@strawberry.type
class NotificationConnection:
    edges: List[NotificationEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class CreatorCardEdge:
    cursor: str
    node: CreatorCardType


@strawberry.type
class CreatorCardConnection:
    edges: List[CreatorCardEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class EndorsementEdge:
    cursor: str
    node: EndorsementType


@strawberry.type
class EndorsementConnection:
    edges: List[EndorsementEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class LiveStreamEdge:
    cursor: str
    node: LiveStreamType


@strawberry.type
class LiveStreamConnection:
    edges: List[LiveStreamEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class BrandOpportunityEdge:
    cursor: str
    node: BrandOpportunityType


@strawberry.type
class BrandOpportunityConnection:
    edges: List[BrandOpportunityEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class SearchResultEdge:
    cursor: str
    node: SearchResultType


@strawberry.type
class SearchResultConnection:
    edges: List[SearchResultEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class ReportEdge:
    cursor: str
    node: ReportType


@strawberry.type
class ReportConnection:
    edges: List[ReportEdge]
    page_info: PageInfo
    total_count: int


# ── Root Query ───────────────────────────────────────────────────────────────


@strawberry.type
class Query:
    # -- Health --
    @strawberry.field
    def health(self) -> str:
        """Simple health check."""
        return "ok"

    # -- Auth (Feature 14) --
    @strawberry.field
    async def me(self, info: StrawberryInfo[AppContext, None]) -> UserType:
        """Get the currently authenticated user. Requires valid JWT."""
        user: User = info.context.require_auth()
        return _user_to_gql(user)

    # -- Profiles (Feature 4) --
    @strawberry.field
    async def profile(
        self,
        info: StrawberryInfo[AppContext, None],
        user_id: Optional[UUIDScalar] = None,
        username: Optional[str] = None,
    ) -> Optional[ProfileType]:
        """Get a user's public profile by user ID or username."""
        return await _profile(info.context, user_id, username)

    @strawberry.field
    async def profiles(
        self,
        info: StrawberryInfo[AppContext, None],
        user_ids: Optional[List[UUIDScalar]] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> CreatorCardConnection:
        """List creator profiles."""
        return await _profiles(info.context, user_ids, first, after)

    # -- Feed (Feature 5) --
    @strawberry.field
    async def feed(
        self,
        info: StrawberryInfo[AppContext, None],
        filter: Optional[FeedFilter] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> PostConnection:
        """Personalized feed for the authenticated user."""
        return await _feed(info.context, filter, first, after)

    @strawberry.field
    async def post(self, info: StrawberryInfo[AppContext, None], id: UUIDScalar) -> Optional[PostType]:
        """Get a specific post by ID."""
        return await _post(info.context, id)

    @strawberry.field
    async def user_posts(
        self,
        info: StrawberryInfo[AppContext, None],
        user_id: UUIDScalar,
        first: int = 20,
        after: Optional[str] = None,
    ) -> PostConnection:
        """Get posts by a specific user."""
        return await _user_posts(info.context, user_id, first, after)

    # -- Collaboration (Feature 1) --
    @strawberry.field
    async def my_collaborations(
        self,
        info: StrawberryInfo[AppContext, None],
        status: Optional[CollaborationStatus] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> CollaborationConnection:
        """List collaborations for the authenticated user."""
        return await _my_collaborations(info.context, status, first, after)

    @strawberry.field
    async def collaboration_marketplace(
        self,
        info: StrawberryInfo[AppContext, None],
        tags: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> CollaborationConnection:
        """Browse the collaboration marketplace."""
        return await _collaboration_marketplace(info.context, tags, content_type, first, after)

    @strawberry.field
    async def collaboration(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> Optional[CollaborationType]:
        """Get a single collaboration by ID."""
        return await _collaboration(info.context, id)

    # -- Messaging (Feature 6) --
    @strawberry.field
    async def conversations(
        self,
        info: StrawberryInfo[AppContext, None],
        first: int = 20,
        after: Optional[str] = None,
    ) -> ConversationConnection:
        """List conversations for the authenticated user."""
        return await _conversations(info.context, first, after)

    @strawberry.field
    async def messages(
        self,
        info: StrawberryInfo[AppContext, None],
        conversation_id: UUIDScalar,
        first: int = 50,
        after: Optional[str] = None,
    ) -> MessageConnection:
        """Get messages for a conversation."""
        return await _messages(info.context, conversation_id, first, after)

    # -- Notifications (Feature 11) --
    @strawberry.field
    async def notifications(
        self,
        info: StrawberryInfo[AppContext, None],
        unread_only: bool = False,
        first: int = 20,
        after: Optional[str] = None,
    ) -> NotificationConnection:
        """Notifications for the authenticated user."""
        return await _notifications(info.context, unread_only, first, after)

    @strawberry.field
    async def unread_notification_count(self, info: StrawberryInfo[AppContext, None]) -> int:
        """Count of unread notifications."""
        return await _unread_notification_count(info.context)

    # -- Reputation (Feature 3) --
    @strawberry.field
    async def reputation(
        self, info: StrawberryInfo[AppContext, None], user_id: UUIDScalar
    ) -> Optional[ReputationScoreType]:
        """Get a user's reputation score."""
        return await _reputation(info.context, user_id)

    @strawberry.field
    async def endorsements(
        self,
        info: StrawberryInfo[AppContext, None],
        user_id: UUIDScalar,
        category: Optional[str] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> EndorsementConnection:
        """Get endorsements for a user."""
        return await _endorsements(info.context, user_id, category, first, after)

    @strawberry.field
    async def user_badges(
        self, info: StrawberryInfo[AppContext, None], user_id: UUIDScalar
    ) -> List[UserBadgeType]:
        """Get a user's earned badges."""
        return await _user_badges(info.context, user_id)

    @strawberry.field
    async def badges(self, info: StrawberryInfo[AppContext, None]) -> List[BadgeType]:
        """List all available badge definitions."""
        return await _badges(info.context)

    # -- Live Streaming (Feature 7) --
    @strawberry.field
    async def live_streams(
        self,
        info: StrawberryInfo[AppContext, None],
        first: int = 20,
        after: Optional[str] = None,
    ) -> LiveStreamConnection:
        """Currently active live streams."""
        return await _live_streams(info.context, first, after)

    @strawberry.field
    async def live_stream(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> Optional[LiveStreamType]:
        """Get a specific live stream."""
        return await _live_stream(info.context, id)

    # -- Trending Sounds (Feature 8) --
    @strawberry.field
    async def trending_sounds(
        self, info: StrawberryInfo[AppContext, None], limit: int = 20
    ) -> List[SoundType]:
        """Currently trending sounds."""
        return await _trending_sounds(info.context, limit)

    # -- Creator Discovery (Feature 9) --
    @strawberry.field
    async def discover_creators(
        self,
        info: StrawberryInfo[AppContext, None],
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> CreatorCardConnection:
        """Discover creators matching tags, interests, or free-text query."""
        return await _discover_creators(info.context, query, tags, first, after)

    # -- Brand Partnerships (Feature 10) --
    @strawberry.field
    async def brand_opportunities(
        self,
        info: StrawberryInfo[AppContext, None],
        status: Optional[CollaborationStatus] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> BrandOpportunityConnection:
        """Browse brand partnership opportunities."""
        return await _brand_opportunities(info.context, status, first, after)

    @strawberry.field
    async def brand_opportunity(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> Optional[BrandOpportunityType]:
        """Get a specific brand opportunity."""
        return await _brand_opportunity(info.context, id)

    # -- Search (Feature 12) --
    @strawberry.field
    async def search(
        self,
        info: StrawberryInfo[AppContext, None],
        input: SearchInput,
        first: int = 20,
        after: Optional[str] = None,
    ) -> SearchResultConnection:
        """Platform-wide search across users, posts, sounds, and collaborations."""
        return await _search(info.context, input, first, after)

    # -- Analytics (Feature 13) --
    @strawberry.field
    async def creator_analytics(
        self, info: StrawberryInfo[AppContext, None], period: AnalyticsPeriod
    ) -> AnalyticsSummaryType:
        """Get analytics summary for the authenticated creator."""
        return await _creator_analytics(info.context, period)

    @strawberry.field
    async def post_analytics(
        self, info: StrawberryInfo[AppContext, None], post_id: UUIDScalar
    ) -> Optional[PostAnalyticsType]:
        """Get analytics for a specific post."""
        return await _post_analytics(info.context, post_id)

    # -- Trust & Safety (Feature 14) --
    @strawberry.field
    async def my_reports(
        self,
        info: StrawberryInfo[AppContext, None],
        first: int = 20,
        after: Optional[str] = None,
    ) -> ReportConnection:
        """Get reports submitted by the authenticated user."""
        return await _my_reports(info.context, first, after)


# ── Root Mutation ────────────────────────────────────────────────────────────


@strawberry.type
class Mutation:
    # -- Auth --
    @strawberry.mutation
    async def register(
        self, info: StrawberryInfo[AppContext, None], input: RegisterInput
    ) -> AuthPayloadType:
        """Register a new user and return JWT tokens."""
        return await _register(info.context, input)

    @strawberry.mutation
    async def login(
        self, info: StrawberryInfo[AppContext, None], input: LoginInput
    ) -> AuthPayloadType:
        """Login with email and password. Returns JWT tokens."""
        return await _login(info.context, input)

    @strawberry.mutation
    async def refresh_token(
        self, info: StrawberryInfo[AppContext, None], refresh_token: str
    ) -> AuthPayloadType:
        """Refresh an expired access token using a valid refresh token."""
        return await _refresh_token(info.context, refresh_token)

    @strawberry.mutation
    async def logout(self, info: StrawberryInfo[AppContext, None]) -> bool:
        """Logout — blacklists the current token."""
        return await _logout(info.context)

    # -- Profiles --
    @strawberry.mutation
    async def update_profile(
        self, info: StrawberryInfo[AppContext, None], input: UpdateProfileInput
    ) -> ProfileType:
        """Update the authenticated user's profile."""
        return await _update_profile(info.context, input)

    # -- Content --
    @strawberry.mutation
    async def create_post(
        self, info: StrawberryInfo[AppContext, None], input: CreatePostInput
    ) -> PostType:
        """Create a new post."""
        return await _create_post(info.context, input)

    @strawberry.mutation
    async def delete_post(self, info: StrawberryInfo[AppContext, None], id: UUIDScalar) -> bool:
        """Delete a post (soft delete)."""
        return await _delete_post(info.context, id)

    @strawberry.mutation
    async def like_post(self, info: StrawberryInfo[AppContext, None], post_id: UUIDScalar) -> int:
        """Like or unlike a post. Returns the new like count."""
        return await _like_post(info.context, post_id)

    @strawberry.mutation
    async def update_post(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar, input: UpdatePostInput
    ) -> PostType:
        """Update an existing post."""
        return await _update_post(info.context, id, input)

    @strawberry.mutation
    async def share_post(
        self, info: StrawberryInfo[AppContext, None], post_id: UUIDScalar
    ) -> PostType:
        """Share a post to the current user's feed."""
        return await _share_post(info.context, post_id)

    @strawberry.mutation
    async def create_comment(
        self, info: StrawberryInfo[AppContext, None], input: CreateCommentInput
    ) -> CommentType:
        """Add a comment to a post."""
        return await _create_comment(info.context, input)

    @strawberry.mutation
    async def delete_comment(self, info: StrawberryInfo[AppContext, None], id: UUIDScalar) -> bool:
        """Delete a comment."""
        return await _delete_comment(info.context, id)

    # -- Collaboration --
    @strawberry.mutation
    async def create_collaboration(
        self, info: StrawberryInfo[AppContext, None], input: CreateCollaborationInput
    ) -> CollaborationType:
        """Create a collaboration proposal."""
        return await _create_collaboration(info.context, input)

    @strawberry.mutation
    async def accept_collaboration(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> CollaborationParticipantType:
        """Accept a collaboration invitation."""
        return await _accept_collaboration(info.context, id)

    @strawberry.mutation
    async def decline_collaboration(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> bool:
        """Decline a collaboration invitation."""
        return await _decline_collaboration(info.context, id)

    @strawberry.mutation
    async def update_collaboration(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar, input: UpdateCollaborationInput
    ) -> CollaborationType:
        """Update an existing collaboration."""
        return await _update_collaboration(info.context, id, input)

    @strawberry.mutation
    async def add_milestone(
        self, info: StrawberryInfo[AppContext, None], input: AddMilestoneInput
    ) -> MilestoneType:
        """Add a milestone to a collaboration."""
        return await _add_milestone(info.context, input)

    @strawberry.mutation
    async def update_milestone(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar, input: UpdateMilestoneInput
    ) -> MilestoneType:
        """Update a milestone."""
        return await _update_milestone(info.context, id, input)

    # -- Messaging --
    @strawberry.mutation
    async def create_conversation(
        self, info: StrawberryInfo[AppContext, None], input: CreateConversationInput
    ) -> ConversationType:
        """Create a new conversation or group chat."""
        return await _create_conversation(info.context, input)

    @strawberry.mutation
    async def send_message(
        self, info: StrawberryInfo[AppContext, None], input: SendMessageInput
    ) -> MessageType:
        """Send a message in a conversation."""
        return await _send_message(info.context, input)

    # -- Notifications --
    @strawberry.mutation
    async def mark_notification_read(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> bool:
        """Mark a notification as read."""
        return await _mark_notification_read(info.context, id)

    @strawberry.mutation
    async def mark_all_notifications_read(self, info: StrawberryInfo[AppContext, None]) -> bool:
        """Mark all notifications as read."""
        return await _mark_all_notifications_read(info.context)

    # -- Reputation --
    @strawberry.mutation
    async def endorse_user(
        self, info: StrawberryInfo[AppContext, None], input: EndorseUserInput
    ) -> EndorsementType:
        """Endorse another user."""
        return await _endorse_user(info.context, input)

    # -- Live Streaming --
    @strawberry.mutation
    async def start_live_stream(
        self, info: StrawberryInfo[AppContext, None], title: str
    ) -> LiveStreamType:
        """Start a live stream."""
        return await _start_live_stream(info.context, title)

    @strawberry.mutation
    async def end_live_stream(
        self, info: StrawberryInfo[AppContext, None], id: UUIDScalar
    ) -> LiveStreamType:
        """End a live stream."""
        return await _end_live_stream(info.context, id)

    # -- Brand Partnerships --
    @strawberry.mutation
    async def create_brand_opportunity(
        self, info: StrawberryInfo[AppContext, None], input: CreateBrandOpportunityInput
    ) -> BrandOpportunityType:
        """Create a brand partnership opportunity."""
        return await _create_brand_opportunity(info.context, input)

    @strawberry.mutation
    async def apply_to_brand_opportunity(
        self, info: StrawberryInfo[AppContext, None], input: ApplyToBrandInput
    ) -> BrandApplicationType:
        """Apply to a brand partnership opportunity."""
        return await _apply_to_brand_opportunity(info.context, input)

    # -- Trust & Safety --
    @strawberry.mutation
    async def report_content(
        self, info: StrawberryInfo[AppContext, None], input: ReportContentInput
    ) -> ReportType:
        """Report content or a user."""
        return await _report_content(info.context, input)


# ── Subscriptions ────────────────────────────────────────────────────────────


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def feed_updated(self, info: StrawberryInfo[AppContext, None]) -> AsyncIterator[PostType]:
        """Real-time feed updates when new posts are created."""
        # TODO: wire Redis/RabbitMQ pub-sub for feed events
        raise NotImplementedError("Subscription not yet wired")

    @strawberry.subscription
    async def collaboration_updated(
        self, info: StrawberryInfo[AppContext, None], collaboration_id: UUIDScalar
    ) -> AsyncIterator[CollaborationType]:
        """Real-time collaboration status changes."""
        raise NotImplementedError("Subscription not yet wired")

    @strawberry.subscription
    async def message_received(
        self, info: StrawberryInfo[AppContext, None]
    ) -> AsyncIterator[MessageType]:
        """New message received in any conversation the user participates in."""
        raise NotImplementedError("Subscription not yet wired")

    @strawberry.subscription
    async def notification_received(
        self, info: StrawberryInfo[AppContext, None]
    ) -> AsyncIterator[NotificationTypeDef]:
        """New notification for the authenticated user."""
        raise NotImplementedError("Subscription not yet wired")

    @strawberry.subscription
    async def badge_earned(
        self, info: StrawberryInfo[AppContext, None]
    ) -> AsyncIterator[UserBadgeType]:
        """Badge earned by the authenticated user."""
        raise NotImplementedError("Subscription not yet wired")

    @strawberry.subscription
    async def live_stream_updated(
        self, info: StrawberryInfo[AppContext, None], live_stream_id: UUIDScalar
    ) -> AsyncIterator[LiveStreamType]:
        """Live stream status changes for a specific stream."""
        raise NotImplementedError("Subscription not yet wired")


# ── Auth Resolvers ───────────────────────────────────────────────────────────
# Real implementations wired to features/auth/*.
# All other resolvers below are feature stubs that will be filled in as each
# feature module is built.


def _user_to_gql(user: User) -> UserType:
    """Map a SQLAlchemy ``User`` ORM instance to the strawberry ``UserType``."""
    return UserType(
        id=user.id,
        email=user.email,
        username=user.username,
        role=UserRole(user.role.value) if user.role else UserRole.USER,
        status=AccountStatus(user.status.value) if user.status else AccountStatus.PENDING_VERIFICATION,
        email_verified=user.email_verified,
        mfa_enabled=user.mfa_enabled,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _profile_to_gql(profile) -> ProfileType:
    """Map a SQLAlchemy ``Profile`` ORM instance to the strawberry ``ProfileType``."""
    return ProfileType(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        cover_image_url=profile.cover_image_url,
        website_url=profile.website_url,
        location=profile.location,
        social_links=profile.social_links,
        tags=profile.tags,
        follower_count=profile.follower_count,
        following_count=profile.following_count,
        collaboration_count=profile.collaboration_count,
        total_likes=profile.total_likes,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _post_to_gql(post) -> PostType:
    """Map a SQLAlchemy ``Post`` ORM instance to the strawberry ``PostType``."""
    return PostType(
        id=post.id,
        user_id=post.user_id,
        content_type=ContentType(post.content_type.value) if post.content_type else ContentType.POST,
        status=ContentStatus(post.status.value) if post.status else ContentStatus.DRAFT,
        title=post.title,
        body=post.body,
        caption=post.caption,
        tags=post.tags,
        mentions=post.mentions,
        sound_track=post.sound_track,
        like_count=post.like_count,
        comment_count=post.comment_count,
        share_count=post.share_count,
        view_count=post.view_count,
        scheduled_at=datetime.fromisoformat(post.scheduled_at) if post.scheduled_at else None,
        published_at=datetime.fromisoformat(post.published_at) if post.published_at else None,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _collaboration_to_gql(collab) -> CollaborationType:
    """Map a SQLAlchemy ``Collaboration`` ORM instance to the strawberry ``CollaborationType``."""
    return CollaborationType(
        id=collab.id,
        initiator_id=collab.initiator_id,
        title=collab.title,
        description=collab.description,
        status=CollaborationStatus(collab.status.value) if collab.status else CollaborationStatus.PROPOSED,
        content_type=collab.content_type,
        platform=collab.platform,
        tags=collab.tags,
        budget_min=collab.budget_min,
        budget_max=collab.budget_max,
        budget_currency=collab.budget_currency,
        proposed_at=datetime.fromisoformat(collab.proposed_at) if collab.proposed_at else None,
        started_at=datetime.fromisoformat(collab.started_at) if collab.started_at else None,
        completed_at=datetime.fromisoformat(collab.completed_at) if collab.completed_at else None,
        created_at=collab.created_at,
        updated_at=collab.updated_at,
    )


def _participant_to_gql(participant) -> CollaborationParticipantType:
    """Map a SQLAlchemy ``CollaborationParticipant`` to the strawberry type."""
    return CollaborationParticipantType(
        id=participant.id,
        collaboration_id=participant.collaboration_id,
        user_id=participant.user_id,
        role=participant.role,
        accepted=participant.accepted,
        accepted_at=datetime.fromisoformat(participant.accepted_at) if participant.accepted_at else None,
    )


def _milestone_to_gql(milestone) -> MilestoneType:
    """Map a SQLAlchemy ``Milestone`` to the strawberry type."""
    return MilestoneType(
        id=milestone.id,
        collaboration_id=milestone.collaboration_id,
        title=milestone.title,
        description=milestone.description,
        status=MilestoneStatus(milestone.status.value) if milestone.status else MilestoneStatus.PENDING,
        due_date=datetime.fromisoformat(milestone.due_date) if milestone.due_date else None,
        completed_at=datetime.fromisoformat(milestone.completed_at) if milestone.completed_at else None,
        created_at=milestone.created_at,
        updated_at=milestone.updated_at,
    )


def _conversation_to_gql(conversation) -> ConversationType:
    """Map a SQLAlchemy ``Conversation`` to the strawberry type."""
    return ConversationType(
        id=conversation.id,
        title=conversation.title,
        is_group=conversation.is_group,
        last_message_at=datetime.fromisoformat(conversation.last_message_at) if conversation.last_message_at else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _message_to_gql(message) -> MessageType:
    """Map a SQLAlchemy ``Message`` to the strawberry type."""
    return MessageType(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content_type=MessageTypeEnum(message.content_type.value) if message.content_type else MessageTypeEnum.TEXT,
        body=message.body,
        media_url=message.media_url,
        status=MessageStatus(message.status.value) if message.status else MessageStatus.SENT,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


def _notification_to_gql(notification) -> NotificationType:
    """Map a SQLAlchemy ``Notification`` to the strawberry type."""
    return NotificationType(
        id=notification.id,
        recipient_id=notification.recipient_id,
        actor_id=notification.actor_id,
        type=NotificationTypeEnum(notification.type.value) if notification.type else NotificationTypeEnum.SYSTEM,
        status=NotificationStatus(notification.status.value) if notification.status else NotificationStatus.UNREAD,
        title=notification.title,
        body=notification.body,
        link=notification.link,
        read_at=datetime.fromisoformat(notification.read_at) if notification.read_at else None,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )


async def _my_collaborations(ctx, status, first, after) -> CollaborationConnection:
    """Resolve myCollaborations query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    
    repo = CollaborationRepository(ctx.db)
    
    # Convert status enum to model enum if provided
    status_filter = None
    if status:
        from app.models.collaboration import CollaborationStatus as ModelCollaborationStatus
        status_filter = ModelCollaborationStatus(status.value)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    collabs = await repo.get_for_user(
        user_id=ctx.user.id,
        status=status_filter,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(collabs) > first
    if has_next_page:
        collabs = collabs[:first]
    
    # Build edges
    edges = [
        CollaborationEdge(
            node=_collaboration_to_gql(c),
            cursor=str(c.id),
        )
        for c in collabs
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,  # Simplified for now
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return CollaborationConnection(edges=edges, page_info=page_info)


async def _register(ctx: AppContext, input: RegisterInput) -> AuthPayloadType:
    from features.auth.password import hash_password, check_password_strength
    from features.auth.jwt import create_access_token, create_refresh_token
    from repositories.user_repository import UserRepository

    is_valid, errors = check_password_strength(input.password)
    if not is_valid:
        raise ValueError("Password too weak: " + "; ".join(errors))

    user_repo = UserRepository(ctx.db)
    if await user_repo.get_by_email(input.email):
        raise ValueError("Email already registered")
    if await user_repo.get_by_username(input.username):
        raise ValueError("Username already taken")

    new_user = User(
        email=input.email,
        username=input.username,
        hashed_password=hash_password(input.password),
        role="user",
        status="pending_verification",
    )
    await user_repo.create(new_user)
    await ctx.db.commit()
    await ctx.db.refresh(new_user)

    access_token = create_access_token(new_user)
    refresh_token = create_refresh_token(new_user)

    return AuthPayloadType(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=_user_to_gql(new_user),
    )


async def _login(ctx: AppContext, input: LoginInput) -> AuthPayloadType:
    from features.auth.password import verify_password
    from features.auth.jwt import create_access_token, create_refresh_token
    from repositories.user_repository import UserRepository
    from app.models.user import AccountStatus

    user_repo = UserRepository(ctx.db)
    user = await user_repo.get_by_email(input.email)
    if not user or not verify_password(input.password, user.hashed_password):
        raise ValueError("Invalid credentials")
    if user.status != AccountStatus.ACTIVE:
        raise ValueError(f"Account is {user.status.value}")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return AuthPayloadType(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=_user_to_gql(user),
    )


async def _refresh_token(ctx: AppContext, refresh_token_str: str) -> AuthPayloadType:
    from features.auth.jwt import decode_token, REFRESH_TOKEN_TYPE as RT, JWTError, create_access_token
    from repositories.user_repository import UserRepository

    try:
        payload = decode_token(refresh_token_str)
    except JWTError:
        raise ValueError("Invalid refresh token")

    if payload.get("type") != RT:
        raise ValueError("Invalid refresh token type")

    user_id = payload.get("sub")
    user_repo = UserRepository(ctx.db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise ValueError("User not found")

    new_access = create_access_token(user)

    return AuthPayloadType(
        access_token=new_access,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=_user_to_gql(user),
    )


async def _logout(ctx: AppContext) -> bool:
    """Logout is a no-op server-side beyond token expiry / client-side removal.
    Token blacklisting via Redis will be added in a future pass."""
    return True


# ── Feature Resolver Stubs ───────────────────────────────────────────────────
# Each stub raises NotImplementedError until its feature repository/service
# is built.  They exist now so that the schema compiles and GraphiQL can
# serve the full type system.  Replace each stub incrementally as features land.


_UNIMPL = " not yet implemented — feature module pending"


async def _profile(ctx, user_id, username) -> Optional[ProfileType]:
    """Get a user's public profile by user ID or username."""
    from repositories.profile_repository import ProfileRepository

    profile_repo = ProfileRepository(ctx.db)

    profile = None
    if user_id:
        profile = await profile_repo.get_by_user_id(user_id)
    elif username:
        profile = await profile_repo.get_by_username(username)

    return _profile_to_gql(profile) if profile else None


async def _profiles(ctx, user_ids, first, after) -> CreatorCardConnection:
    """List creator profiles."""
    from repositories.profile_repository import ProfileRepository
    
    profile_repo = ProfileRepository(ctx.db)
    
    # For now, just return empty connection
    # TODO: Implement proper pagination and filtering
    return CreatorCardConnection(
        edges=[],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
        total_count=0,
    )


async def _feed(ctx, filter, first, after) -> PostConnection:
    """Resolve feed query - personalized feed for the authenticated user."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.content_repository import PostRepository
    
    repo = PostRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    # Get feed posts (simplified - just gets user's posts for now)
    # In production, this would use algorithm based on follows, interests, etc.
    posts = await repo.get_feed(
        user_id=ctx.user.id,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Apply filters if provided
    if filter:
        if filter.content_type:
            posts = [p for p in posts if p.content_type.value == filter.content_type.value]
        if filter.tags:
            posts = [p for p in posts if p.tags and any(tag in p.tags for tag in filter.tags)]
    
    # Check if there are more results
    has_next_page = len(posts) > first
    if has_next_page:
        posts = posts[:first]
    
    # Build edges
    edges = [
        PostEdge(
            node=_post_to_gql(p),
            cursor=str(p.id),
        )
        for p in posts
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return PostConnection(edges=edges, page_info=page_info)


async def _post(ctx, id) -> Optional[PostType]:
    """Get a specific post by ID."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.content_repository import PostRepository
    
    try:
        post_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid post ID")
    
    repo = PostRepository(ctx.db)
    post = await repo.get_by_id(post_id)
    
    if not post:
        return None
    
    return _post_to_gql(post)


async def _user_posts(ctx, user_id, first, after) -> PostConnection:
    """Get posts by a specific user."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.content_repository import PostRepository
    
    try:
        uid = UUID_type(user_id)
    except ValueError:
        raise ValueError("Invalid user ID")
    
    repo = PostRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    posts = await repo.get_by_user_id(
        user_id=uid,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(posts) > first
    if has_next_page:
        posts = posts[:first]
    
    # Build edges
    edges = [
        PostEdge(
            node=_post_to_gql(p),
            cursor=str(p.id),
        )
        for p in posts
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return PostConnection(edges=edges, page_info=page_info)


async def _my_collaborations(ctx, status, first, after) -> CollaborationConnection:
    raise NotImplementedError("myCollaborations" + _UNIMPL)


async def _collaboration_marketplace(ctx, tags, content_type, first, after) -> CollaborationConnection:
    """Resolve collaborationMarketplace query."""
    from uuid import UUID as UUID_type
    
    repo = CollaborationRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    collabs = await repo.get_marketplace(
        tags=tags,
        content_type=content_type,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(collabs) > first
    if has_next_page:
        collabs = collabs[:first]
    
    # Build edges
    edges = [
        CollaborationEdge(
            node=_collaboration_to_gql(c),
            cursor=str(c.id),
        )
        for c in collabs
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return CollaborationConnection(edges=edges, page_info=page_info)


async def _collaboration(ctx, id) -> Optional[CollaborationType]:
    """Resolve collaboration query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    
    try:
        collab_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid collaboration ID")
    
    repo = CollaborationRepository(ctx.db)
    collab = await repo.get_by_id(collab_id)
    
    if not collab:
        return None
    
    # Check if user has access (initiator or participant)
    is_initiator = collab.initiator_id == ctx.user.id
    
    if not is_initiator:
        # Check if user is a participant
        participant = await repo.get_participant(collab_id, ctx.user.id)
        if not participant:
            raise ValueError("Access denied to this collaboration")
    
    return _collaboration_to_gql(collab)


async def _conversations(ctx, first, after) -> ConversationConnection:
    """Resolve conversations query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    
    from repositories.messaging_repository import ConversationRepository
    
    repo = ConversationRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    conversations = await repo.get_for_user(
        user_id=ctx.user.id,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(conversations) > first
    if has_next_page:
        conversations = conversations[:first]
    
    # Build edges
    edges = [
        ConversationEdge(
            node=_conversation_to_gql(c),
            cursor=str(c.id),
        )
        for c in conversations
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return ConversationConnection(edges=edges, page_info=page_info)


async def _messages(ctx, conversation_id, first, after) -> MessageConnection:
    """Resolve messages query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    
    from repositories.messaging_repository import ConversationRepository, MessageRepository
    
    try:
        conv_id = UUID_type(conversation_id)
    except ValueError:
        raise ValueError("Invalid conversation ID")
    
    # Verify user is participant in conversation
    conv_repo = ConversationRepository(ctx.db)
    participant = await conv_repo.get_participant(conv_id, ctx.user.id)
    if not participant:
        raise ValueError("Access denied to this conversation")
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    msg_repo = MessageRepository(ctx.db)
    messages = await msg_repo.get_for_conversation(
        conversation_id=conv_id,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(messages) > first
    if has_next_page:
        messages = messages[:first]
    
    # Build edges
    edges = [
        MessageEdge(
            node=_message_to_gql(m),
            cursor=str(m.id),
        )
        for m in messages
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return MessageConnection(edges=edges, page_info=page_info)


async def _notifications(ctx, unread_only, first, after) -> NotificationConnection:
    """Resolve notifications query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    
    from repositories.notification_repository import NotificationRepository
    
    repo = NotificationRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    notifications = await repo.get_for_user(
        user_id=ctx.user.id,
        unread_only=unread_only,
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(notifications) > first
    if has_next_page:
        notifications = notifications[:first]
    
    # Build edges
    edges = [
        NotificationEdge(
            node=_notification_to_gql(n),
            cursor=str(n.id),
        )
        for n in notifications
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return NotificationConnection(edges=edges, page_info=page_info)


async def _unread_notification_count(ctx) -> int:
    """Resolve unreadNotificationCount query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from repositories.notification_repository import NotificationRepository
    
    repo = NotificationRepository(ctx.db)
    count = await repo.get_unread_count(ctx.user.id)
    return count


async def _reputation(ctx, user_id) -> Optional[ReputationScoreType]:
    """Get reputation score for a user."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.reputation_repository import ReputationRepository
    
    try:
        uid = UUID_type(user_id)
    except ValueError:
        raise ValueError("Invalid user ID")
    
    repo = ReputationRepository(ctx.db)
    score = await repo.get_reputation_score(uid)
    
    if not score:
        return None
    
    return ReputationScoreType(
        id=score.id,
        user_id=score.user_id,
        overall_score=score.overall_score,
        content_score=score.content_score,
        collaboration_score=score.collaboration_score,
        endorsement_count=score.endorsement_count,
        badge_count=score.badge_count,
        last_calculated_at=score.last_calculated_at,
    )


async def _endorsements(ctx, user_id, category, first, after) -> EndorsementConnection:
    """Get endorsements for a user."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.reputation_repository import ReputationRepository
    from app.models.reputation import EndorsementStatus
    
    try:
        uid = UUID_type(user_id)
    except ValueError:
        raise ValueError("Invalid user ID")
    
    repo = ReputationRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    # Get endorsements
    status_filter = EndorsementStatus.APPROVED  # Only show approved
    endorsements = await repo.get_endorsements_for_user(
        user_id=uid,
        status=status_filter,
        limit=first + 1,
        before_id=before_id,
    )
    
    # Filter by category if provided
    if category:
        endorsements = [e for e in endorsements if e.skill == category]
    
    # Check if there are more results
    has_next_page = len(endorsements) > first
    if has_next_page:
        endorsements = endorsements[:first]
    
    # Build edges
    edges = [
        EndorsementEdge(
            node=EndorsementType(
                id=e.id,
                endorser_id=e.endorser_id,
                endorsed_user_id=e.endorsed_user_id,
                skill=e.skill,
                comment=e.comment,
                status=e.status,
                created_at=e.created_at,
            ),
            cursor=str(e.id),
        )
        for e in endorsements
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return EndorsementConnection(edges=edges, page_info=page_info)


async def _user_badges(ctx, user_id) -> List[UserBadgeType]:
    """Get badges earned by a user."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.reputation_repository import ReputationRepository
    
    try:
        uid = UUID_type(user_id)
    except ValueError:
        raise ValueError("Invalid user ID")
    
    repo = ReputationRepository(ctx.db)
    user_badges = await repo.get_user_badges(uid)
    
    return [
        UserBadgeType(
            id=ub.id,
            user_id=ub.user_id,
            badge_id=ub.badge_id,
            awarded_at=ub.awarded_at,
        )
        for ub in user_badges
    ]


async def _badges(ctx) -> List[BadgeType]:
    """List all available badge definitions."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from repositories.reputation_repository import ReputationRepository
    
    repo = ReputationRepository(ctx.db)
    badges = await repo.get_available_badges()
    
    return [
        BadgeType(
            id=b.id,
            name=b.name,
            description=b.description,
            icon_url=b.icon_url,
            category=b.category,
            required_score=b.required_score,
        )
        for b in badges
    ]


async def _live_streams(ctx, first, after) -> LiveStreamConnection:
    """Get currently active live streams."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.live_stream_repository import LiveStreamRepository
    
    repo = LiveStreamRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    streams = await repo.get_active_streams(
        limit=first + 1,  # Fetch one extra to check hasNextPage
        before_id=before_id,
    )
    
    # Check if there are more results
    has_next_page = len(streams) > first
    if has_next_page:
        streams = streams[:first]
    
    # Build edges
    edges = [
        LiveStreamEdge(
            node=LiveStreamType(
                id=s.id,
                user_id=s.user_id,
                title=s.title,
                status=s.status,
                viewer_count=s.viewer_count,
                started_at=s.started_at,
                ended_at=s.ended_at,
            ),
            cursor=str(s.id),
        )
        for s in streams
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return LiveStreamConnection(edges=edges, page_info=page_info)


async def _live_stream(ctx, id) -> Optional[LiveStreamType]:
    """Get a specific live stream by ID."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.live_stream_repository import LiveStreamRepository
    
    try:
        stream_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid live stream ID")
    
    repo = LiveStreamRepository(ctx.db)
    stream = await repo.get_by_id(stream_id)
    
    if not stream:
        return None
    
    return LiveStreamType(
        id=stream.id,
        user_id=stream.user_id,
        title=stream.title,
        status=stream.status,
        viewer_count=stream.viewer_count,
        started_at=stream.started_at,
        ended_at=stream.ended_at,
    )


async def _trending_sounds(ctx, limit) -> List[SoundType]:
    """Get currently trending sounds."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    # This is a placeholder - in production would query from a sounds table
    # For now, return empty list or mock data
    return []


async def _discover_creators(ctx, query, tags, first, after) -> CreatorCardConnection:
    """Discover creators matching tags, interests, or free-text query."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.profile_repository import ProfileRepository
    from repositories.user_repository import UserRepository
    
    repo = ProfileRepository(ctx.db)
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    # Get profiles (simplified discovery - would use algorithm in production)
    profiles = await repo.get_all(limit=first + 1)
    
    # Filter by tags if provided
    if tags:
        profiles = [p for p in profiles if p.tags and any(tag in p.tags for tag in tags)]
    
    # Filter by query if provided
    if query:
        profiles = [p for p in profiles if query.lower() in (p.display_name or "").lower() or 
                   query.lower() in (p.bio or "").lower()]
    
    # Check if there are more results
    has_next_page = len(profiles) > first
    if has_next_page:
        profiles = profiles[:first]
    
    # Build edges
    edges = []
    user_repo = UserRepository(ctx.db)
    for profile in profiles:
        creator_card = CreatorCard(
            user_id=profile.user_id,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            bio=profile.bio,
            tags=profile.tags,
            follower_count=profile.follower_count,
            following_count=profile.following_count,
        )
        edges.append(
            CreatorCardEdge(
                node=creator_card,
                cursor=str(profile.id),
            )
        )
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return CreatorCardConnection(edges=edges, page_info=page_info)


async def _brand_opportunities(ctx, status, first, after) -> BrandOpportunityConnection:
    """Browse brand partnership opportunities."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    # Placeholder - would need BrandOpportunity repository
    # For now, return empty connection
    page_info = PageInfo(
        has_next_page=False,
        has_previous_page=False,
        start_cursor=None,
        end_cursor=None,
    )
    
    return BrandOpportunityConnection(edges=[], page_info=page_info)


async def _brand_opportunity(ctx, id) -> Optional[BrandOpportunityType]:
    """Get a specific brand opportunity."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    # Placeholder - would query from database
    return None


async def _search(ctx, input, first, after) -> SearchResultConnection:
    """Platform-wide search across users, posts, sounds, and collaborations."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.user_repository import UserRepository
    from repositories.content_repository import PostRepository
    from repositories.collaboration_repository import CollaborationRepository
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    results = []
    
    # Search users
    if not input.types or "USER" in [t.value for t in input.types]:
        user_repo = UserRepository(ctx.db)
        # This is a simplified search - in production would use full-text search
        users = await user_repo.search_by_username(input.query, limit=first//3)
        for user in users:
            results.append(SearchResult(
                id=user.id,
                type=SearchResultType.USER,
                title=user.username,
                snippet=user.email,
                created_at=user.created_at,
            ))
    
    # Search posts
    if not input.types or "POST" in [t.value for t in input.types]:
        post_repo = PostRepository(ctx.db)
        posts = await post_repo.search_by_content(input.query, limit=first//3)
        for post in posts:
            results.append(SearchResult(
                id=post.id,
                type=SearchResultType.POST,
                title=post.title or "Post",
                snippet=post.body[:100] if post.body else "",
                created_at=post.created_at,
            ))
    
    # Search collaborations
    if not input.types or "COLLABORATION" in [t.value for t in input.types]:
        collab_repo = CollaborationRepository(ctx.db)
        collabs = await collab_repo.search_by_title(input.query, limit=first//3)
        for collab in collabs:
            results.append(SearchResult(
                id=collab.id,
                type=SearchResultType.COLLABORATION,
                title=collab.title,
                snippet=collab.description[:100] if collab.description else "",
                created_at=collab.created_at,
            ))
    
    # Sort by relevance (simplified - just by created_at)
    results.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    has_next_page = len(results) > first
    if has_next_page:
        results = results[:first]
    
    # Build edges
    edges = [
        SearchResultEdge(
            node=r,
            cursor=str(r.id),
        )
        for r in results
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return SearchResultConnection(edges=edges, page_info=page_info)


async def _creator_analytics(ctx, period) -> AnalyticsSummaryType:
    """Get analytics summary for the authenticated creator."""
    user = ctx.require_auth()
    
    from repositories.content_repository import PostRepository
    from repositories.profile_repository import ProfileRepository
    
    post_repo = PostRepository(ctx.db)
    profile_repo = ProfileRepository(ctx.db)
    
    # Get user's posts
    posts = await post_repo.get_by_user_id(user.id, limit=100)
    
    # Calculate analytics
    total_posts = len(posts)
    total_views = sum(p.view_count for p in posts)
    total_likes = sum(p.like_count for p in posts)
    total_comments = sum(p.comment_count for p in posts)
    total_shares = sum(p.share_count for p in posts)
    
    # Get profile for follower info
    profile = await profile_repo.get_by_user_id(user.id)
    follower_change = profile.follower_count if profile else 0
    
    # Calculate engagement rate (simplified)
    engagement_rate = 0.0
    if total_views > 0:
        engagement_rate = (total_likes + total_comments + total_shares) / total_views * 100
    
    return AnalyticsSummaryType(
        user_id=user.id,
        period=period,
        total_posts=total_posts,
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        follower_change=follower_change,
        top_post_id=None,  # TODO: Find top post
        engagement_rate=engagement_rate,
    )


async def _post_analytics(ctx, post_id) -> Optional[PostAnalyticsType]:
    """Get analytics for a specific post."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from repositories.content_repository import PostRepository
    
    try:
        pid = UUID_type(post_id)
    except ValueError:
        raise ValueError("Invalid post ID")
    
    repo = PostRepository(ctx.db)
    post = await repo.get_by_id(pid)
    
    if not post:
        return None
    
    # Check ownership
    if post.user_id != ctx.user.id:
        raise PermissionError("Not your post")
    
    # Calculate reach and impressions (simplified)
    reach = post.view_count * 2 if post.view_count > 0 else 0
    impressions = post.view_count
    
    return PostAnalyticsType(
        post_id=pid,
        views=post.view_count,
        likes=post.like_count,
        comments=post.comment_count,
        shares=post.share_count,
        reach=reach,
        impressions=impressions,
        engagement_rate=0.0,  # TODO: Calculate
        demographics=None,  # TODO: Add demographics
    )


async def _my_reports(ctx, first, after) -> ReportConnection:
    """Get reports filed by the authenticated user."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import UUID as UUID_type
    from app.models.notification import Report, ReportStatus
    from sqlalchemy import select
    
    # Parse cursor for pagination
    before_id = None
    if after:
        try:
            before_id = UUID_type(after)
        except ValueError:
            raise ValueError("Invalid cursor")
    
    # Get reports by this user
    stmt = select(Report).where(
        Report.reporter_id == ctx.user.id
    )
    if before_id:
        stmt = stmt.where(Report.id < before_id)
    stmt = stmt.order_by(Report.created_at.desc()).limit(first + 1)
    
    result = await ctx.db.execute(stmt)
    reports = list(result.scalars().all())
    
    # Check if there are more results
    has_next_page = len(reports) > first
    if has_next_page:
        reports = reports[:first]
    
    # Build edges
    edges = [
        ReportEdge(
            node=ReportType(
                id=r.id,
                reporter_id=r.reporter_id,
                reported_user_id=r.reported_user_id,
                content_type=r.content_type,
                content_id=r.content_id,
                reason=r.reason,
                description=r.description,
                status=r.status,
                created_at=r.created_at,
                updated_at=r.updated_at,
            ),
            cursor=str(r.id),
        )
        for r in reports
    ]
    
    # Build page info
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=False,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    
    return ReportConnection(edges=edges, page_info=page_info)


async def _update_profile(ctx, input) -> ProfileType:
    """Update the authenticated user's profile."""
    from repositories.profile_repository import ProfileRepository
    from app.models.user import Profile

    user = ctx.require_auth()
    profile_repo = ProfileRepository(ctx.db)

    profile = await profile_repo.get_by_user_id(user.id)
    if not profile:
        # Auto-create profile on first update
        profile = Profile(
            user_id=user.id,
            display_name=user.username,
        )
        await profile_repo.create(profile)

    # Apply updates from input
    for field in (
        "display_name", "bio", "avatar_url", "cover_image_url",
        "website_url", "location", "social_links", "tags",
    ):
        value = getattr(input, field, None)
        if value is not None:
            setattr(profile, field, value)

    await profile_repo.update(profile)
    await ctx.db.commit()

    return _profile_to_gql(profile)


async def _create_post(ctx, input) -> PostType:
    """Create a new post."""
    from repositories.content_repository import PostRepository
    from app.models.content import Post, ContentType as CT, ContentStatus as CS

    user = ctx.require_auth()
    post_repo = PostRepository(ctx.db)

    post = Post(
        user_id=user.id,
        content_type=CT(input.content_type.value) if input.content_type else CT.POST,
        status=CS.DRAFT,
        title=input.title,
        body=input.body,
        caption=input.caption,
        tags=input.tags,
        sound_track=input.sound_track,
        scheduled_at=input.scheduled_at.isoformat() if input.scheduled_at else None,
    )
    await post_repo.create(post)
    await ctx.db.commit()

    return _post_to_gql(post)


async def _delete_post(ctx, id) -> bool:
    """Soft-delete a post. Only the author or admin can delete."""
    from repositories.content_repository import PostRepository

    user = ctx.require_auth()
    post_repo = PostRepository(ctx.db)

    post = await post_repo.get_by_id(id)
    if not post:
        raise ValueError("Post not found")
    if post.user_id != user.id and user.role.value not in ("admin",):
        raise PermissionError("Only the post author can delete this post")

    success = await post_repo.soft_delete(id)
    if success:
        await ctx.db.commit()
    return success


async def _like_post(ctx, post_id) -> int:
    """Like a post. Returns the new like count."""
    from repositories.content_repository import PostRepository

    ctx.require_auth()
    post_repo = PostRepository(ctx.db)
    new_count = await post_repo.like_post(post_id)
    await ctx.db.commit()
    return new_count


async def _update_post(ctx, id, input) -> PostType:
    """Update an existing post."""
    from repositories.content_repository import PostRepository
    from uuid import UUID as UUID_type

    user = ctx.require_auth()
    post_repo = PostRepository(ctx.db)

    try:
        post_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid post ID")

    post = await post_repo.get_by_id(post_id)
    if not post:
        raise ValueError("Post not found")
    
    # Check ownership
    if post.user_id != user.id and user.role.value not in ("admin",):
        raise PermissionError("Only the post author can update this post")

    # Apply updates from input
    for field in ("title", "body", "caption", "tags", "sound_track", "scheduled_at"):
        value = getattr(input, field, None)
        if value is not None:
            if field == "scheduled_at" and value:
                setattr(post, field, value.isoformat())
            else:
                setattr(post, field, value)

    post.updated_at = datetime.now(timezone.utc)
    await post_repo.update(post)
    await ctx.db.commit()
    return _post_to_gql(post)


async def _share_post(ctx, post_id) -> PostType:
    """Share a post to the current user's feed."""
    from repositories.content_repository import PostRepository
    from app.models.content import Post, ContentType as CT, ContentStatus as CS
    from uuid import uuid4, UUID as UUID_type

    user = ctx.require_auth()
    post_repo = PostRepository(ctx.db)

    try:
        original_post_id = UUID_type(post_id)
    except ValueError:
        raise ValueError("Invalid post ID")

    # Verify original post exists
    original_post = await post_repo.get_by_id(original_post_id)
    if not original_post:
        raise ValueError("Post not found")

    # Create a new share post
    share_post = Post(
        id=uuid4(),
        user_id=user.id,
        content_type=CT.SHARE,
        status=CS.PUBLISHED,
        title=f"Shared: {original_post.title}" if original_post.title else "Shared post",
        body=f"Shared from {original_post.user_id}",
        tags=original_post.tags,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    await post_repo.create(share_post)
    await ctx.db.commit()
    
    # Return the original post with share info
    return _post_to_gql(original_post)


async def _create_comment(ctx, input) -> CommentType:
    """Create a comment on a post."""
    from repositories.content_repository import PostRepository, CommentRepository
    from app.models.content import Comment

    user = ctx.require_auth()
    post_repo = PostRepository(ctx.db)
    comment_repo = CommentRepository(ctx.db)

    # Verify post exists
    post = await post_repo.get_by_id(input.post_id)
    if not post:
        raise ValueError("Post not found")

    comment = Comment(
        post_id=input.post_id,
        user_id=user.id,
        body=input.body,
        parent_id=input.parent_id,
    )
    await comment_repo.create(comment)
    
    # Increment comment count on post
    post.comment_count += 1
    
    await ctx.db.commit()
    
    # Map to GraphQL type
    return CommentType(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        body=comment.body,
        parent_id=comment.parent_id,
        like_count=comment.like_count,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


async def _delete_comment(ctx, id) -> bool:
    """Delete a comment. Only the author can delete."""
    from repositories.content_repository import CommentRepository, PostRepository
    from uuid import UUID as UUID_type

    user = ctx.require_auth()
    comment_repo = CommentRepository(ctx.db)
    post_repo = PostRepository(ctx.db)

    try:
        comment_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid comment ID")

    comment = await comment_repo.get_by_id(comment_id)
    if not comment:
        raise ValueError("Comment not found")
    
    # Check ownership
    if comment.user_id != user.id and user.role.value not in ("admin",):
        raise PermissionError("Only the comment author can delete this comment")

    # Decrement post comment count
    post = await post_repo.get_by_id(comment.post_id)
    if post and post.comment_count > 0:
        post.comment_count -= 1

    success = await comment_repo.soft_delete(comment_id)
    if success:
        await ctx.db.commit()
    return success


async def _create_collaboration(ctx, input) -> CollaborationType:
    """Create a new collaboration proposal."""
    from repositories.collaboration_repository import CollaborationRepository
    from app.models.collaboration import Collaboration, CollaborationStatus

    user = ctx.require_auth()
    repo = CollaborationRepository(ctx.db)

    collab = Collaboration(
        initiator_id=user.id,
        title=input.title,
        description=input.description,
        content_type=input.content_type,
        platform=input.platform,
        tags=input.tags,
        budget_min=input.budget_min,
        budget_max=input.budget_max,
        budget_currency=input.budget_currency or "USD",
    )
    await repo.create(collab)

    # Add participants
    for pid in input.participant_ids:
        if pid != user.id:
            participant = CollaborationParticipant(
                collaboration_id=collab.id,
                user_id=pid,
                role="participant",
            )
            await repo.add_participant(participant)

    # Add initiator as accepted participant
    initiator_participant = CollaborationParticipant(
        collaboration_id=collab.id,
        user_id=user.id,
        role="initiator",
        accepted=True,
        accepted_at=datetime.now(timezone.utc).isoformat(),
    )
    await repo.add_participant(initiator_participant)

    await ctx.db.commit()
    await ctx.db.refresh(collab)
    return _collaboration_to_gql(collab)


async def _accept_collaboration(ctx, id) -> CollaborationParticipantType:
    """Accept a collaboration invitation."""
    from repositories.collaboration_repository import CollaborationRepository

    user = ctx.require_auth()
    repo = CollaborationRepository(ctx.db)

    participant = await repo.get_participant(id, user.id)
    if not participant:
        raise ValueError("You are not a participant of this collaboration")

    participant.accepted = True
    participant.accepted_at = datetime.now(timezone.utc).isoformat()
    await repo.update_participant(participant)
    await ctx.db.commit()

    return _participant_to_gql(participant)


async def _decline_collaboration(ctx, id) -> bool:
    """Decline a collaboration invitation."""
    from repositories.collaboration_repository import CollaborationRepository

    user = ctx.require_auth()
    repo = CollaborationRepository(ctx.db)

    participant = await repo.get_participant(id, user.id)
    if not participant:
        raise ValueError("You are not a participant of this collaboration")

    await repo.remove_participant(participant)
    await ctx.db.commit()
    return True


async def _update_collaboration(ctx, id, input) -> CollaborationType:
    """Update an existing collaboration."""
    from repositories.collaboration_repository import CollaborationRepository
    from uuid import UUID as UUID_type

    user = ctx.require_auth()
    repo = CollaborationRepository(ctx.db)

    try:
        collab_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid collaboration ID")

    collab = await repo.get_by_id(collab_id)
    if not collab:
        raise ValueError("Collaboration not found")
    
    # Check ownership (only initiator can update)
    if collab.initiator_id != user.id and user.role.value not in ("admin",):
        raise PermissionError("Only the collaboration initiator can update it")

    # Apply updates from input
    for field in ("title", "description", "content_type", "platform", "tags", "budget_min", "budget_max", "budget_currency"):
        value = getattr(input, field, None)
        if value is not None:
            setattr(collab, field, value)

    collab.updated_at = datetime.now(timezone.utc)
    await repo.update(collab)
    await ctx.db.commit()
    return _collaboration_to_gql(collab)


async def _add_milestone(ctx, input) -> MilestoneType:
    """Add a milestone to a collaboration."""
    from repositories.collaboration_repository import CollaborationRepository
    from app.models.collaboration import Milestone, MilestoneStatus
    from uuid import uuid4

    user = ctx.require_auth()
    repo = CollaborationRepository(ctx.db)

    # Verify collaboration exists and user is participant
    collab = await repo.get_by_id(input.collaboration_id)
    if not collab:
        raise ValueError("Collaboration not found")
    
    participant = await repo.get_participant(input.collaboration_id, user.id)
    if not participant and collab.initiator_id != user.id:
        raise PermissionError("Not a participant in this collaboration")

    # Create milestone
    milestone = Milestone(
        id=uuid4(),
        collaboration_id=input.collaboration_id,
        title=input.title,
        description=input.description,
        status=MilestoneStatus.PENDING,
        due_date=input.due_date.isoformat() if input.due_date else None,
    )
    
    await repo.add_milestone(milestone)
    await ctx.db.commit()
    return _milestone_to_gql(milestone)


async def _update_milestone(ctx, id, input) -> MilestoneType:
    """Update a milestone."""
    from repositories.collaboration_repository import CollaborationRepository
    from uuid import UUID as UUID_type
    from app.models.collaboration import MilestoneStatus

    user = ctx.require_auth()
    repo = CollaborationRepository(ctx.db)

    try:
        milestone_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid milestone ID")

    # Get milestone and verify access
    milestone = await repo.get_milestone_by_id(milestone_id)
    if not milestone:
        raise ValueError("Milestone not found")
    
    # Verify user has access to the collaboration
    collab = await repo.get_by_id(milestone.collaboration_id)
    if not collab:
        raise ValueError("Collaboration not found")
    
    participant = await repo.get_participant(milestone.collaboration_id, user.id)
    if not participant and collab.initiator_id != user.id:
        raise PermissionError("Not a participant in this collaboration")

    # Apply updates
    if input.title is not None:
        milestone.title = input.title
    if input.description is not None:
        milestone.description = input.description
    if input.status is not None:
        milestone.status = MilestoneStatus(input.status.value)
    if input.due_date is not None:
        milestone.due_date = input.due_date.isoformat()

    await repo.update_milestone(milestone)
    await ctx.db.commit()
    return _milestone_to_gql(milestone)


async def _create_conversation(ctx, input) -> ConversationType:
    """Resolve createConversation mutation."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import uuid4
    from datetime import datetime, timezone
    from repositories.messaging_repository import ConversationRepository, ConversationParticipant
    from app.models.messaging import Conversation as ConversationModel
    
    # Validate participant IDs
    if not input.participant_ids:
        raise ValueError("At least one participant required")
    
    # Create conversation
    conversation = ConversationModel(
        id=uuid4(),
        title=input.title,
        is_group=input.is_group if input.is_group is not None else False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    conv_repo = ConversationRepository(ctx.db)
    conversation = await conv_repo.create(conversation)
    
    # Add participants (including current user)
    all_participant_ids = list(input.participant_ids)
    if ctx.user.id not in all_participant_ids:
        all_participant_ids.append(ctx.user.id)
    
    for user_id in all_participant_ids:
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id,
        )
        await conv_repo.add_participant(participant)
    
    await ctx.db.commit()
    return _conversation_to_gql(conversation)


async def _send_message(ctx, input) -> MessageType:
    """Resolve sendMessage mutation."""
    if not ctx.user:
        raise ValueError("Authentication required")
    
    from uuid import uuid4
    from datetime import datetime, timezone
    from repositories.messaging_repository import ConversationRepository, MessageRepository
    from app.models.messaging import Message as MessageModel, MessageStatus, MessageType as ModelMessageType
    
    # Verify user is participant in conversation
    conv_repo = ConversationRepository(ctx.db)
    participant = await conv_repo.get_participant(input.conversation_id, ctx.user.id)
    if not participant:
        raise ValueError("Access denied to this conversation")
    
    # Create message
    message = MessageModel(
        id=uuid4(),
        conversation_id=input.conversation_id,
        sender_id=ctx.user.id,
        content_type=ModelMessageType.TEXT,  # Default to text
        body=input.body,
        media_url=input.media_url,
        status=MessageStatus.SENT,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    msg_repo = MessageRepository(ctx.db)
    message = await msg_repo.create(message)
    
    # Update conversation's last_message_at
    conversation = await conv_repo.get_by_id(input.conversation_id)
    if conversation:
        conversation.last_message_at = datetime.now(timezone.utc)
        conversation.updated_at = datetime.now(timezone.utc)
    
    await ctx.db.commit()
    return _message_to_gql(message)


async def _mark_notification_read(ctx, id) -> bool:
    """Mark a notification as read."""
    from repositories.notification_repository import NotificationRepository
    from uuid import UUID as UUID_type

    user = ctx.require_auth()
    repo = NotificationRepository(ctx.db)

    try:
        notification_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid notification ID")

    notification = await repo.get_by_id(notification_id)
    if not notification:
        raise ValueError("Notification not found")
    
    # Check ownership
    if notification.recipient_id != user.id:
        raise PermissionError("Not your notification")

    await repo.mark_as_read(notification)
    await ctx.db.commit()
    return True


async def _mark_all_notifications_read(ctx) -> bool:
    """Mark all notifications as read."""
    user = ctx.require_auth()
    from repositories.notification_repository import NotificationRepository
    
    repo = NotificationRepository(ctx.db)
    count = await repo.mark_all_as_read(user.id)
    await ctx.db.commit()
    return True


async def _endorse_user(ctx, input) -> EndorsementType:
    """Endorse another user."""
    from repositories.reputation_repository import ReputationRepository
    from app.models.reputation import Endorsement, EndorsementStatus
    from uuid import uuid4

    user = ctx.require_auth()
    
    # Prevent self-endorsement
    if user.id == input.endorsed_user_id:
        raise ValueError("Cannot endorse yourself")
    
    repo = ReputationRepository(ctx.db)
    
    # Create endorsement
    endorsement = Endorsement(
        id=uuid4(),
        endorser_id=user.id,
        endorsed_user_id=input.endorsed_user_id,
        skill=input.skill,
        comment=input.comment,
        status=EndorsementStatus.PENDING,  # Requires approval or auto-approve
    )
    
    await repo.create_endorsement(endorsement)
    await ctx.db.commit()
    
    # Map to GraphQL type
    return EndorsementType(
        id=endorsement.id,
        endorser_id=endorsement.endorser_id,
        endorsed_user_id=endorsement.endorsed_user_id,
        skill=endorsement.skill,
        comment=endorsement.comment,
        status=EndorsementStatus(endorsement.status.value),
        created_at=endorsement.created_at,
    )


async def _start_live_stream(ctx, title) -> LiveStreamType:
    """Start a live stream."""
    from repositories.live_stream_repository import LiveStreamRepository
    from app.models.content import LiveStream, LiveStreamStatus
    from uuid import uuid4

    user = ctx.require_auth()
    repo = LiveStreamRepository(ctx.db)

    # Create live stream
    live_stream = LiveStream(
        id=uuid4(),
        user_id=user.id,
        title=title,
        status=LiveStreamStatus.LIVE,
        viewer_count=0,
        started_at=datetime.now(timezone.utc),
    )

    await repo.create(live_stream)
    await ctx.db.commit()

    # Map to GraphQL type
    return LiveStreamType(
        id=live_stream.id,
        user_id=live_stream.user_id,
        title=live_stream.title,
        status=LiveStreamStatus(live_stream.status.value),
        viewer_count=live_stream.viewer_count,
        started_at=live_stream.started_at,
        ended_at=live_stream.ended_at,
    )


async def _end_live_stream(ctx, id) -> LiveStreamType:
    """End a live stream."""
    from repositories.live_stream_repository import LiveStreamRepository
    from uuid import UUID as UUID_type

    user = ctx.require_auth()
    repo = LiveStreamRepository(ctx.db)

    try:
        stream_id = UUID_type(id)
    except ValueError:
        raise ValueError("Invalid live stream ID")

    live_stream = await repo.get_by_id(stream_id)
    if not live_stream:
        raise ValueError("Live stream not found")

    # Check ownership
    if live_stream.user_id != user.id and user.role.value not in ("admin",):
        raise PermissionError("Only the stream owner can end this stream")

    # End the stream
    live_stream.status = LiveStreamStatus.ENDED
    live_stream.ended_at = datetime.now(timezone.utc)

    await repo.update(live_stream)
    await ctx.db.commit()

    return LiveStreamType(
        id=live_stream.id,
        user_id=live_stream.user_id,
        title=live_stream.title,
        status=LiveStreamStatus(live_stream.status.value),
        viewer_count=live_stream.viewer_count,
        started_at=live_stream.started_at,
        ended_at=live_stream.ended_at,
    )


async def _create_brand_opportunity(ctx, input) -> BrandOpportunityType:
    """Create a brand partnership opportunity."""
    from app.models.content import BrandOpportunity, BrandOpportunityStatus
    from uuid import uuid4

    user = ctx.require_auth()
    
    # Create brand opportunity
    opportunity = BrandOpportunity(
        id=uuid4(),
        creator_id=user.id,
        title=input.title,
        description=input.description,
        budget=input.budget,
        requirements=input.requirements,
        status=BrandOpportunityStatus.OPEN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    ctx.db.add(opportunity)
    await ctx.db.commit()
    await ctx.db.refresh(opportunity)
    
    return BrandOpportunityType(
        id=opportunity.id,
        creator_id=opportunity.creator_id,
        title=opportunity.title,
        description=opportunity.description,
        budget=opportunity.budget,
        requirements=opportunity.requirements,
        status=opportunity.status,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at,
    )


async def _apply_to_brand_opportunity(ctx, input) -> BrandApplicationType:
    """Apply to a brand partnership opportunity."""
    from app.models.content import BrandApplication, BrandApplicationStatus
    from uuid import uuid4

    user = ctx.require_auth()
    
    # Create brand application
    application = BrandApplication(
        id=uuid4(),
        opportunity_id=input.opportunity_id,
        applicant_id=user.id,
        pitch=input.pitch,
        status=BrandApplicationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    ctx.db.add(application)
    await ctx.db.commit()
    await ctx.db.refresh(application)
    
    return BrandApplicationType(
        id=application.id,
        opportunity_id=application.opportunity_id,
        applicant_id=application.applicant_id,
        pitch=application.pitch,
        status=application.status,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


async def _report_content(ctx, input) -> ReportType:
    """Report content or a user."""
    from app.models.notification import Report, ReportStatus, ReportReason
    from uuid import uuid4

    user = ctx.require_auth()
    
    # Create report
    report = Report(
        id=uuid4(),
        reporter_id=user.id,
        reported_user_id=input.reported_user_id,
        content_type=input.content_type,
        content_id=input.content_id,
        reason=ReportReason(input.reason.value) if input.reason else ReportReason.OTHER,
        description=input.description,
        status=ReportStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    ctx.db.add(report)
    await ctx.db.commit()
    await ctx.db.refresh(report)
    
    return ReportType(
        id=report.id,
        reporter_id=report.reporter_id,
        reported_user_id=report.reported_user_id,
        content_type=report.content_type,
        content_id=report.content_id,
        reason=report.reason,
        description=report.description,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


# ── Error Handling Extension ─────────────────────────────────────────────────


class ConnextionZErrorExtension(strawberry.extensions.SchemaExtension):
    """
    Custom Strawberry extension that catches resolver exceptions and converts
    them to structured GraphQL errors with proper extensions.

    Catches:
    - PermissionError → UNAUTHENTICATED (401)
    - ValueError → VALIDATION_ERROR (400)
    - NotImplementedError → NOT_IMPLEMENTED (501)
    - Other exceptions → INTERNAL_ERROR (500)
    """

    def on_execute(self):
        yield
        # After execution, check for errors and enrich them
        if self.execution_context.errors:
            for error in self.execution_context.errors:
                # Add request ID if available
                if hasattr(self.execution_context, "request_id"):
                    error.extensions = error.extensions or {}
                    error.extensions["requestId"] = self.execution_context.request_id

                # Map Python exceptions to GraphQL error codes
                original = error.original_error
                if isinstance(original, PermissionError):
                    error.extensions = error.extensions or {}
                    error.extensions["code"] = "UNAUTHENTICATED"
                    error.extensions["statusCode"] = 401
                elif isinstance(original, ValueError):
                    error.extensions = error.extensions or {}
                    error.extensions["code"] = "VALIDATION_ERROR"
                    error.extensions["statusCode"] = 400
                elif isinstance(original, NotImplementedError):
                    error.extensions = error.extensions or {}
                    error.extensions["code"] = "NOT_IMPLEMENTED"
                    error.extensions["statusCode"] = 501
                else:
                    error.extensions = error.extensions or {}
                    error.extensions["code"] = "INTERNAL_ERROR"
                    error.extensions["statusCode"] = 500


# ── Schema Assembly ──────────────────────────────────────────────────────────


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[ConnextionZErrorExtension],
)


# ── Router Factory ───────────────────────────────────────────────────────────


def create_graphql_router(
    session_factory: Callable[[], AsyncSession],
) -> GraphQLRouter[AppContext]:
    """Create a FastAPI-compatible GraphQL router."""
    from features.auth.jwt import decode_token, JWTError
    from repositories.user_repository import UserRepository

    async def get_context(
        request: Request,
        response: Response,
    ) -> AppContext:
        """Build the per-request ``AppContext``.

        1. Create a fresh ``AsyncSession`` from the session factory.
        2. If ``Authorization: Bearer <token>`` is present, decode the JWT
           and load the ``User``. Auth errors are swallowed so public queries
           still work; protected resolvers call ``ctx.require_auth()``.
        """
        db = session_factory()

        current_user: User | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                    user_repo = UserRepository(db)
                    current_user = await user_repo.get_by_id(user_id)
            except (JWTError, ValueError):
                pass

        return AppContext(db=db, current_user=current_user)

    return GraphQLRouter[AppContext](
        schema,
        context_getter=get_context,
        graphiql=True,
        subscription_protocols=["graphql-ws"],
    )
