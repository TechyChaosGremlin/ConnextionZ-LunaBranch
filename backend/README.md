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
