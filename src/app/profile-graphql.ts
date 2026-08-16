export type GraphQLPost = {
  id: string;
  thumbnail: string;
  caption: string;
  views: number;
  likes: number;
  collabWith?: string | null;
};

export type GraphQLPlaylist = {
  id: string;
  title: string;
  cover: string;
  itemLabel: string;
  plays: number;
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

const GRAPHQL_URL = "http://127.0.0.1:8000/graphql";

async function graphqlRequest<T>(query: string, variables?: Record<string, unknown>): Promise<T | null> {
  try {
    const res = await fetch(GRAPHQL_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
          caption
          views
          likes
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
          caption
          views
          likes
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
