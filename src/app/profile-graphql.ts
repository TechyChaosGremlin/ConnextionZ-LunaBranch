export type GraphQLPost = {
  id: string;
  thumbnail: string;
  mediaUrl?: string | null;
  caption: string;
  views: number;
  likes: number;
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
};

export type GraphQLFeedItem = GraphQLPost & {
  creator: GraphQLProfileSummary;
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
  posts?: GraphQLPost[] | null;
  playlists?: GraphQLPlaylist[] | null;
};

import { BACKEND_API_URL, GRAPHQL_ENDPOINT } from "./api-config";

export async function uploadMediaFile(file: Blob, filename: string): Promise<string | null> {
  try {
    const form = new FormData();
    form.append("file", file, filename);
    const response = await fetch(`${BACKEND_API_URL}/api/media/upload`, {
      method: "POST",
      body: form,
      credentials: "include",
    });
    if (!response.ok) return null;
    const data = await response.json();
    return typeof data.url === "string" ? new URL(data.url, BACKEND_API_URL).toString() : null;
  } catch (error) {
    console.warn("Media upload unavailable", error);
    return null;
  }
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
          creator { id username displayName avatarUrl avatarColor verified }
        }
      }
    }
  `, { cursor, limit });
  return data?.feed ?? null;
}

async function graphqlRequest<T>(query: string, variables?: Record<string, unknown>): Promise<T | null> {
  try {
    const res = await fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",  // Include cookies for session auth
      body: JSON.stringify({ query, variables }),
    });

    if (!res.ok) {
      console.warn("GraphQL request failed", res.status, await res.text());
      return null;
    }

    const json = await res.json();
    if (json.errors?.length) {
      console.warn("GraphQL errors", json.errors);
      return null;
    }

    return json.data as T;
  } catch (error) {
    console.warn("GraphQL unavailable", error);
    return null;
  }
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
  thumbnail: string;
  mediaUrl?: string;
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
`;

export async function fetchMyFollowing(): Promise<GraphQLProfileSummary[] | null> {
  const data = await graphqlRequest<{ myFollowing: GraphQLProfileSummary[] }>(`
    query MyFollowing { myFollowing { ${profileSummaryFields} } }
  `);
  return data?.myFollowing ?? null;
}

export async function fetchMyFollowers(): Promise<GraphQLProfileSummary[] | null> {
  const data = await graphqlRequest<{ myFollowers: GraphQLProfileSummary[] }>(`
    query MyFollowers { myFollowers { ${profileSummaryFields} } }
  `);
  return data?.myFollowers ?? null;
}

export async function followProfile(identifier: string): Promise<boolean | null> {
  const data = await graphqlRequest<{ follow: { following: boolean } }>(`
    mutation Follow($username: String!) {
      follow(username: $username) { following followers followingCount }
    }
  `, { username: identifier });
  return data?.follow.following ?? null;
}

export async function unfollowProfile(identifier: string): Promise<boolean | null> {
  const data = await graphqlRequest<{ unfollow: { following: boolean } }>(`
    mutation Unfollow($username: String!) {
      unfollow(username: $username) { following followers followingCount }
    }
  `, { username: identifier });
  return data?.unfollow.following ?? null;
}
