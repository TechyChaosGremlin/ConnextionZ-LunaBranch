export type GraphQLPost = {
  id: string;
  thumbnail: string;
  mediaUrl?: string | null;
  caption: string;
  views: number;
  likes: number;
  isLiked?: boolean | null;
  hashtags?: string[] | null;
  audio?: string | null;
  visibility?: string | null;
  allowComments?: boolean | null;
  allowCollabs?: boolean | null;
  durationSec?: number | null;
  comments?: number | null;
  shares?: number | null;
  saves?: number | null;
  collabWith?: string | null;
};

export type GraphQLNotification = {
  id: string;
  type: string;
  actor: string | null;
  text: string;
  postId: string | null;
  createdAt: number;
  read: boolean;
};

export type UploadedPostMedia = {
  id: string;
  url: string;
  contentType: string;
};

export type GraphQLPlaylist = {
  id: string;
  title: string;
  cover: string;
  itemLabel: string;
  plays: number;
};

export type GraphQLProfileSummary = {
  id: string;
  username: string;
  displayName: string;
  avatarUrl?: string | null;
  avatarColor?: string | null;
  verified?: boolean | null;
  collabScore?: number | null;
  collabCount?: number | null;
  followers?: number | null;
  following?: number | null;
  openToCollab?: boolean | null;
  isFollowing?: boolean | null;
};

export type GraphQLFeedItem = GraphQLPost & {
  creator: GraphQLProfileSummary;
};

export type GraphQLHashtagResult = {
  tag: string;
  posts: number;
  views: number;
};

export type GraphQLSound = {
  id: string;
  title: string;
  creator: string;
  creatorAvatar: string;
  artwork: string;
  genre: string;
  videoCount: number;
  totalPlays: number;
  rank: number;
  growthPct: number;
  duration: string;
  bpm: number;
};

export type GraphQLProfile = {
  id: string;
  username: string;
  displayName: string;
  avatarUrl?: string | null;
  avatarColor?: string | null;
  bio?: string | null;
  location?: string | null;
  website?: string | null;
  verified?: boolean | null;
  online?: boolean | null;
  collabStatus?: string | null;
  collabScore?: number | null;
  collabCount?: number | null;
  followers?: number | null;
  following?: number | null;
  openToCollab?: boolean | null;
  responseTime?: string | null;
  isFollowing?: boolean | null;
  posts?: GraphQLPost[] | null;
  playlists?: GraphQLPlaylist[] | null;
};

import { BACKEND_API_URL, GRAPHQL_ENDPOINT } from "./api-config";
import { type Result } from "./auth-store";


async function uploadFile(file: Blob, filename: string, kind: "media" | "avatar"): Promise<Record<string, unknown> | null> {
  try {
    const form = new FormData();
    form.append("file", file, filename);
    const endpoint = kind === "avatar" ? `${BACKEND_API_URL}/api/avatar/upload` : `${BACKEND_API_URL}/api/media/upload`;
    const response = await fetch(endpoint, {
      method: "POST",
      body: form,
      credentials: "include",
    });
    if (!response.ok) return null;
    return await response.json() as Record<string, unknown>;
  } catch (error) {
    console.warn("Media upload unavailable", error);
    return null;
  }
}


export async function fetchNotificationsFromApi(): Promise<Result<GraphQLNotification[]>> {
  const result = await graphqlRequestResult<{
    notifications: GraphQLNotification[];
  }>(`
    query Notifications {
      notifications {
        id
        type
        actor
        text
        postId
        createdAt
        read
      }
    }
  `);

  if (!result.ok) {
    return result;
  }

  return {
    ok: true,
    value: result.value.notifications,
  };
}

export async function markNotificationReadFromApi(
  id: string,
): Promise<Result<boolean>> {
  const result = await graphqlRequestResult<{
    markNotificationRead: boolean;
  }>(
    `
      mutation MarkNotificationRead($id: ID!) {
        markNotificationRead(id: $id)
      }
    `,
    { id },
  );

  if (!result.ok) {
    return result;
  }

  return {
    ok: true,
    value: result.value.markNotificationRead,
  };
}

export async function markAllNotificationsReadFromApi(): Promise<Result<boolean>> {
  const result = await graphqlRequestResult<{
    markAllNotificationsRead: boolean;
  }>(`
    mutation MarkAllNotificationsRead {
      markAllNotificationsRead
    }
  `);

  if (!result.ok) {
    return result;
  }

  return {
    ok: true,
    value: result.value.markAllNotificationsRead,
  };
}

export async function uploadMediaFile(file: Blob, filename: string, kind: "media" | "avatar" = "media"): Promise<string | null> {
  const data = await uploadFile(file, filename, kind);
  return typeof data?.url === "string" ? new URL(data.url, BACKEND_API_URL).toString() : null;
}

export async function uploadPostMediaFile(file: Blob, filename: string): Promise<UploadedPostMedia | null> {
  const data = await uploadFile(file, filename, "media");
  if (typeof data?.id !== "string" || typeof data.url !== "string" || typeof data.contentType !== "string") {
    return null;
  }
  return {
    id: data.id,
    url: new URL(data.url, BACKEND_API_URL).toString(),
    contentType: data.contentType,
  };
}

export async function fetchFeedPageFromApi(cursor: string | null, limit = 10): Promise<{
  items: GraphQLFeedItem[];
  nextCursor: string | null;
} | null> {
  const data = await graphqlRequest<{ feed: { items: GraphQLFeedItem[]; nextCursor: string | null } }>(`
    query Feed($cursor: String, $limit: Int!) {
      feed(cursor: $cursor, limit: $limit) {
        nextCursor
        items {
          id
          thumbnail
          mediaUrl
          caption
          views
          likes
          isLiked
          hashtags
          audio
          visibility
          allowComments
          allowCollabs
          durationSec
          comments
          shares
          saves
          collabWith
          creator { id username displayName avatarUrl avatarColor verified collabScore collabCount followers following openToCollab }
        }
      }
    }
  `, { cursor, limit });
  return data?.feed ?? null;
}

export async function searchPosts(query: string, limit = 20): Promise<GraphQLFeedItem[] | null> {
  const data = await graphqlRequest<{ searchPosts: GraphQLFeedItem[] }>(`
    query SearchPosts($query: String!, $limit: Int!) {
      searchPosts(query: $query, limit: $limit) {
        id thumbnail mediaUrl caption views likes isLiked hashtags audio visibility
        allowComments allowCollabs durationSec comments shares saves collabWith
        creator { id username displayName avatarUrl avatarColor verified }
      }
    }
  `, { query, limit });
  return data?.searchPosts ?? null;
}

export async function searchHashtags(query: string, limit = 20): Promise<GraphQLHashtagResult[] | null> {
  const data = await graphqlRequest<{ searchHashtags: GraphQLHashtagResult[] }>(`
    query SearchHashtags($query: String!, $limit: Int!) {
      searchHashtags(query: $query, limit: $limit) { tag posts views }
    }
  `, { query, limit });
  return data?.searchHashtags ?? null;
}

export async function fetchTrendingSounds(genre?: string): Promise<GraphQLSound[] | null> {
  const data = await graphqlRequest<{ trendingSounds: GraphQLSound[] }>(`
    query TrendingSounds($genre: String) {
      trendingSounds(genre: $genre) {
        id title creator creatorAvatar artwork genre videoCount totalPlays
        rank growthPct duration bpm
      }
    }
  `, { genre });
  return data?.trendingSounds ?? null;
}

/**
 * Runs a GraphQL request and reports *why* it failed — a dropped connection,
 * an HTTP error, or a GraphQL error — instead of collapsing every case into
 * `null`. Callers that need to tell "no more results" apart from "the request
 * failed" (pagination, in particular) should use this over `graphqlRequest`.
 */
async function graphqlRequestResult<T>(query: string, variables?: Record<string, unknown>): Promise<Result<T>> {
  let res: Response;
  try {
    res = await fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",  // Include cookies for session auth
      body: JSON.stringify({ query, variables }),
    });
  } catch (error) {
    console.warn("GraphQL unavailable", error);
    return { ok: false, error: "Could not reach the server. Check your connection and try again." };
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    console.warn("GraphQL request failed", res.status, body);
    return {
      ok: false,
      error: res.status === 401
        ? "Your session has expired. Sign in again to continue."
        : res.status >= 500
          ? "The server ran into a problem. Try again in a moment."
          : "That request could not be completed.",
    };
  }

  let json: { data?: T; errors?: { message?: string }[] };
  try {
    json = await res.json();
  } catch (error) {
    console.warn("GraphQL response was not valid JSON", error);
    return { ok: false, error: "The server sent back something unexpected." };
  }

  if (json.errors?.length) {
    console.warn("GraphQL errors", json.errors);
    return { ok: false, error: json.errors[0]?.message || "That request could not be completed." };
  }

  return { ok: true, value: json.data as T };
}

async function graphqlRequest<T>(query: string, variables?: Record<string, unknown>): Promise<T | null> {
  const result = await graphqlRequestResult<T>(query, variables);
  return result.ok ? result.value : null;
}

export async function fetchMeProfile(): Promise<GraphQLProfile | null> {
  const data = await graphqlRequest<{ me: GraphQLProfile | null }>(`
    query MeProfile {
      me {
        id
        username
        displayName
        avatarUrl
        avatarColor
        bio
        location
        website
        verified
        online
        collabStatus
        collabScore
        collabCount
        followers
        following
        openToCollab
        responseTime
        isFollowing
        posts {
          id
          thumbnail
          mediaUrl
          caption
          views
          likes
          hashtags
          audio
          visibility
          allowComments
          allowCollabs
          durationSec
          comments
          shares
          saves
          collabWith
        }
        playlists {
          id
          title
          cover
          itemLabel
          plays
        }
      }
    }
  `);

  return data?.me ?? null;
}

export async function fetchProfileByUsername(username: string): Promise<GraphQLProfile | null> {
  const data = await graphqlRequest<{ profile: GraphQLProfile | null }>(`
    query ProfileByUsername($username: String!) {
      profile(username: $username) {
        id
        username
        displayName
        avatarUrl
        avatarColor
        bio
        location
        website
        verified
        online
        collabStatus
        collabScore
        collabCount
        followers
        following
        openToCollab
        responseTime
        isFollowing
        posts {
          id
          thumbnail
          mediaUrl
          caption
          views
          likes
          hashtags
          audio
          visibility
          allowComments
          allowCollabs
          durationSec
          comments
          shares
          saves
          collabWith
        }
        playlists {
          id
          title
          cover
          itemLabel
          plays
        }
      }
    }
  `, { username });

  return data?.profile ?? null;
}

export async function searchProfiles(query: string, limit = 20): Promise<GraphQLProfileSummary[] | null> {
  const data = await graphqlRequest<{ searchProfiles: GraphQLProfileSummary[] }>(`
    query SearchProfiles($query: String!, $limit: Int!) {
      searchProfiles(query: $query, limit: $limit) {
        ${profileSummaryFields}
      }
    }
  `, { query, limit });
  return data?.searchProfiles ?? null;
}

export type UpdateProfilePatch = {
  username?: string;
  displayName?: string;
  bio?: string;
  location?: string;
  website?: string;
  avatarUrl?: string;
  avatarColor?: string;
  collabStatus?: string;
  openToCollab?: boolean;
};

export async function updateMeProfile(patch: UpdateProfilePatch): Promise<GraphQLProfile | null> {
  const data = await graphqlRequest<{ updateProfile: GraphQLProfile | null }>(`
    mutation UpdateProfile($input: UpdateProfileInput!) {
      updateProfile(input: $input) {
        id
        username
        displayName
        avatarUrl
        avatarColor
        bio
        location
        website
        avatarColor
        collabStatus
        openToCollab
      }
    }
  `, { input: patch });

  return data?.updateProfile ?? null;
}

const postFields = `
  id
  thumbnail
  mediaUrl
  caption
  views
  likes
  isLiked
  hashtags
  audio
  visibility
  allowComments
  allowCollabs
  durationSec
  comments
  shares
  saves
  collabWith
`;

const playlistFields = `
  id
  title
  cover
  itemLabel
  plays
`;

export async function fetchMyPosts(): Promise<GraphQLPost[]> {
  const data = await graphqlRequest<{ myPosts: GraphQLPost[] }>(`
    query MyPosts { myPosts { ${postFields} } }
  `);
  return data?.myPosts ?? [];
}

export async function fetchMyPlaylists(): Promise<GraphQLPlaylist[]> {
  const data = await graphqlRequest<{ myPlaylists: GraphQLPlaylist[] }>(`
    query MyPlaylists { myPlaylists { ${playlistFields} } }
  `);
  return data?.myPlaylists ?? [];
}

export type PostInput = {
  mediaId: string;
  thumbnailMediaId: string;
  caption?: string;
  collabWith?: string;
  hashtags?: string[];
  audio?: string;
  visibility?: string;
  allowComments?: boolean;
  allowCollabs?: boolean;
  durationSec?: number;
};

export type PlaylistInput = {
  title: string;
  cover: string;
  itemLabel: string;
};

export type GraphQLLikeResult = {
  liked: boolean;
  likes: number;
};

export async function likePost(id: string): Promise<Result<GraphQLLikeResult>> {
  const result = await graphqlRequestResult<{ likePost: GraphQLLikeResult }>(`
    mutation LikePost($id: ID!) {
      likePost(id: $id) { liked likes }
    }
  `, { id });
  return result.ok ? { ok: true, value: result.value.likePost } : result;
}

export async function unlikePost(id: string): Promise<Result<GraphQLLikeResult>> {
  const result = await graphqlRequestResult<{ unlikePost: GraphQLLikeResult }>(`
    mutation UnlikePost($id: ID!) {
      unlikePost(id: $id) { liked likes }
    }
  `, { id });
  return result.ok ? { ok: true, value: result.value.unlikePost } : result;
}

export async function createPost(input: PostInput): Promise<GraphQLPost | null> {
  const data = await graphqlRequest<{ createPost: GraphQLPost }>(`
    mutation CreatePost($input: PostInput!) {
      createPost(input: $input) { ${postFields} }
    }
  `, { input });
  return data?.createPost ?? null;
}

export async function updatePost(id: string, input: Partial<PostInput>): Promise<GraphQLPost | null> {
  const data = await graphqlRequest<{ updatePost: GraphQLPost }>(`
    mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
      updatePost(id: $id, input: $input) { ${postFields} }
    }
  `, { id, input });
  return data?.updatePost ?? null;
}

export async function deletePost(id: string): Promise<boolean> {
  const data = await graphqlRequest<{ deletePost: boolean }>(`
    mutation DeletePost($id: ID!) { deletePost(id: $id) }
  `, { id });
  return data?.deletePost ?? false;
}

export async function createPlaylist(input: PlaylistInput): Promise<GraphQLPlaylist | null> {
  const data = await graphqlRequest<{ createPlaylist: GraphQLPlaylist }>(`
    mutation CreatePlaylist($input: PlaylistInput!) {
      createPlaylist(input: $input) { ${playlistFields} }
    }
  `, { input });
  return data?.createPlaylist ?? null;
}

export async function updatePlaylist(id: string, input: Partial<PlaylistInput>): Promise<GraphQLPlaylist | null> {
  const data = await graphqlRequest<{ updatePlaylist: GraphQLPlaylist }>(`
    mutation UpdatePlaylist($id: ID!, $input: UpdatePlaylistInput!) {
      updatePlaylist(id: $id, input: $input) { ${playlistFields} }
    }
  `, { id, input });
  return data?.updatePlaylist ?? null;
}

export async function deletePlaylist(id: string): Promise<boolean> {
  const data = await graphqlRequest<{ deletePlaylist: boolean }>(`
    mutation DeletePlaylist($id: ID!) { deletePlaylist(id: $id) }
  `, { id });
  return data?.deletePlaylist ?? false;
}

const profileSummaryFields = `
  id
  username
  displayName
  avatarUrl
  avatarColor
  verified
  collabScore
  collabCount
  followers
  following
  openToCollab
  isFollowing
`;

export async function fetchSuggestedProfiles(limit = 6): Promise<GraphQLProfileSummary[] | null> {
  const data = await graphqlRequest<{ suggestedProfiles: GraphQLProfileSummary[] }>(`
    query SuggestedProfiles($limit: Int!) {
      suggestedProfiles(limit: $limit) { ${profileSummaryFields} }
    }
  `, { limit });
  return data?.suggestedProfiles ?? null;
}

export async function fetchMyFollowing(): Promise<GraphQLProfileSummary[] | null> {
  const data = await graphqlRequest<{ myFollowing: GraphQLProfileSummary[] }>(`
    query MyFollowing { myFollowing { ${profileSummaryFields} } }
  `);
  return data?.myFollowing ?? null;
}

export type GraphQLProfilePage = {
  profiles: GraphQLProfileSummary[];
  nextCursor: string | null;
};

export async function fetchMyFollowingPage(after: string | null, limit = 20): Promise<Result<GraphQLProfilePage>> {
  const result = await graphqlRequestResult<{ myFollowingPage: GraphQLProfilePage }>(`
    query MyFollowingPage($after: String, $limit: Int!) {
      myFollowingPage(after: $after, limit: $limit) {
        nextCursor profiles { ${profileSummaryFields} }
      }
    }
  `, { after, limit });
  return result.ok ? { ok: true, value: result.value.myFollowingPage } : result;
}

export async function fetchMyFollowers(): Promise<GraphQLProfileSummary[] | null> {
  const data = await graphqlRequest<{ myFollowers: GraphQLProfileSummary[] }>(`
    query MyFollowers { myFollowers { ${profileSummaryFields} } }
  `);
  return data?.myFollowers ?? null;
}

export async function fetchMyFollowersPage(after: string | null, limit = 20): Promise<Result<GraphQLProfilePage>> {
  const result = await graphqlRequestResult<{ myFollowersPage: GraphQLProfilePage }>(`
    query MyFollowersPage($after: String, $limit: Int!) {
      myFollowersPage(after: $after, limit: $limit) {
        nextCursor profiles { ${profileSummaryFields} }
      }
    }
  `, { after, limit });
  return result.ok ? { ok: true, value: result.value.myFollowersPage } : result;
}

export async function fetchFollowersPage(username: string, after: string | null, limit = 20): Promise<Result<GraphQLProfilePage>> {
  const result = await graphqlRequestResult<{ followersPage: GraphQLProfilePage }>(`
    query FollowersPage($username: String!, $after: String, $limit: Int!) {
      followersPage(username: $username, after: $after, limit: $limit) {
        nextCursor profiles { ${profileSummaryFields} }
      }
    }
  `, { username, after, limit });
  return result.ok ? { ok: true, value: result.value.followersPage } : result;
}

export async function fetchFollowingPage(username: string, after: string | null, limit = 20): Promise<Result<GraphQLProfilePage>> {
  const result = await graphqlRequestResult<{ followingPage: GraphQLProfilePage }>(`
    query FollowingPage($username: String!, $after: String, $limit: Int!) {
      followingPage(username: $username, after: $after, limit: $limit) {
        nextCursor profiles { ${profileSummaryFields} }
      }
    }
  `, { username, after, limit });
  return result.ok ? { ok: true, value: result.value.followingPage } : result;
}

export type GraphQLFollowResult = {
  following: boolean;
  followers: number;
  followingCount: number;
};

export async function followProfile(identifier: string): Promise<Result<GraphQLFollowResult>> {
  const result = await graphqlRequestResult<{ follow: GraphQLFollowResult }>(`
    mutation Follow($username: String!) {
      follow(username: $username) { following followers followingCount }
    }
  `, { username: identifier });
  return result.ok ? { ok: true, value: result.value.follow } : result;
}

export async function unfollowProfile(identifier: string): Promise<Result<GraphQLFollowResult>> {
  const result = await graphqlRequestResult<{ unfollow: GraphQLFollowResult }>(`
    mutation Unfollow($username: String!) {
      unfollow(username: $username) { following followers followingCount }
    }
  `, { username: identifier });
  return result.ok ? { ok: true, value: result.value.unfollow } : result;
}
