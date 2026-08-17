#!/usr/bin/env python3
"""End-to-end API tests for auth, profiles, sessions, and follows."""

import json
import urllib.error
import urllib.request
import uuid

BASE_URL = "http://127.0.0.1:8002"


def request_json(opener, path, payload, expected_status=200):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(request, timeout=10) as response:
            body = json.loads(response.read().decode())
            assert response.status == expected_status, (response.status, body)
            return body
    except urllib.error.HTTPError as error:
        body = json.loads(error.read().decode())
        assert error.code == expected_status, (error.code, body)
        return body


def graphql(opener, query, variables=None):
    return request_json(opener, "/graphql", {"query": query, "variables": variables or {}})


def assert_graphql_success(result):
    assert not result.get("errors"), result
    return result["data"]


def main():
    suffix = uuid.uuid4().hex[:10]
    email = f"api.test.{suffix}@connextionz.app"
    password = "testpass123"
    username = f"api_test_{suffix}"
    display_name = "API Test Creator"

    anonymous = urllib.request.build_opener()
    session = urllib.request.HTTPCookieProcessor()
    authenticated = urllib.request.build_opener(session)

    print("1. Register account")
    registration = request_json(authenticated, "/auth/register", {
        "email": email,
        "password": password,
        "username": username,
        "display_name": display_name,
    })
    assert registration["ok"] is True
    assert registration["profile"]["username"] == username

    print("2. Login account")
    login = request_json(authenticated, "/auth/login", {
        "email": email,
        "password": password,
    })
    assert login["ok"] is True
    assert login["user"]["email"] == email

    print("3. Query own profile")
    me_query = """
        query { me { username displayName bio location website avatarColor } }
    """
    me = assert_graphql_success(graphql(authenticated, me_query))["me"]
    assert me["username"] == username
    assert me["displayName"] == display_name

    print("4. Update profile")
    update_query = """
        mutation UpdateProfile($input: UpdateProfileInput!) {
          updateProfile(input: $input) {
            username displayName bio location website avatarUrl avatarColor
            collabStatus openToCollab
          }
        }
    """
    updated = assert_graphql_success(graphql(authenticated, update_query, {"input": {
        "displayName": "Updated API Creator",
        "bio": "Persisted by the API test",
        "location": "SQL City",
        "website": "https://example.com",
        "avatarUrl": "https://example.com/avatar.png",
        "avatarColor": "#22c55e",
        "collabStatus": "Open to Collaboration",
        "openToCollab": False,
    }}))["updateProfile"]
    assert updated["displayName"] == "Updated API Creator"
    assert updated["bio"] == "Persisted by the API test"
    assert updated["location"] == "SQL City"
    assert updated["website"] == "https://example.com"
    assert updated["avatarColor"] == "#22c55e"
    assert updated["openToCollab"] is False

    print("5. Follow and unfollow")
    follow_query = """
        mutation Follow($username: String!) {
          follow(username: $username) { following followers followingCount }
        }
    """
    follow = assert_graphql_success(graphql(authenticated, follow_query, {"username": "luna"}))["follow"]
    assert follow["following"] is True
    assert follow["followingCount"] == 1

    following = assert_graphql_success(graphql(
        authenticated, "query { myFollowing { username } }"
    ))["myFollowing"]
    assert any(profile["username"] == "luna" for profile in following)

    unfollow_query = """
        mutation Unfollow($username: String!) {
          unfollow(username: $username) { following followers followingCount }
        }
    """
    unfollow = assert_graphql_success(graphql(authenticated, unfollow_query, {"username": "luna"}))["unfollow"]
    assert unfollow["following"] is False
    assert unfollow["followingCount"] == 0

    print("6. Logout and reject protected requests")
    logout = request_json(authenticated, "/auth/logout", {})
    assert logout["ok"] is True
    after_logout = graphql(authenticated, me_query)
    assert after_logout["data"]["me"] is None

    protected_update = graphql(anonymous, update_query, {"input": {"bio": "must fail"}})
    assert protected_update.get("errors"), protected_update

    protected_follow = graphql(anonymous, follow_query, {"username": "luna"})
    assert protected_follow.get("errors"), protected_follow

    print("7. Reject duplicate email and username")
    duplicate_email = request_json(anonymous, "/auth/register", {
        "email": email,
        "password": password,
        "username": f"other_email_{suffix}",
        "display_name": "Duplicate Email",
    }, expected_status=409)
    assert "detail" in duplicate_email

    duplicate_username = request_json(anonymous, "/auth/register", {
        "email": f"other.username.{suffix}@connextionz.app",
        "password": password,
        "username": username,
        "display_name": "Duplicate Username",
    }, expected_status=409)
    assert "detail" in duplicate_username

    print("API_TESTS_PASSED")


if __name__ == "__main__":
    main()
