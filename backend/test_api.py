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
    target_email = f"api.target.{suffix}@connextionz.app"
    target_username = f"api_target_{suffix}"

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

    target_registration = request_json(anonymous, "/auth/register", {
        "email": target_email,
        "password": password,
        "username": target_username,
        "display_name": "API Target Creator",
    })
    assert target_registration["ok"] is True

    print("3. Query own profile")
    me_query = """
        query { me { username displayName bio location website avatarColor } }
    """
    me = assert_graphql_success(graphql(authenticated, me_query))["me"]
    assert me["username"] == username
    assert me["displayName"] == display_name

    search_query = """
        query SearchProfiles($query: String!) {
          searchProfiles(query: $query) { username displayName }
        }
    """
    search_results = assert_graphql_success(graphql(
        authenticated, search_query, {"query": username}
    ))["searchProfiles"]
    assert any(profile["username"] == username for profile in search_results)

    sounds_query = """
        query { trendingSounds(limit: 3) { id title genre totalPlays } }
    """
    sounds = assert_graphql_success(graphql(
        authenticated, sounds_query
    ))["trendingSounds"]
    assert sounds and sounds[0]["id"] == "s1"

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
        "website": "example.com",
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
    public_profile_query = """
        query Profile($username: String!) {
          profile(username: $username) { username displayName followers following isFollowing }
        }
    """
    before_follow = assert_graphql_success(graphql(
        authenticated, public_profile_query, {"username": target_username}
    ))["profile"]
    assert before_follow["username"] == target_username
    assert before_follow["displayName"] == "API Target Creator"
    assert before_follow["followers"] == 0
    assert before_follow["following"] == 0
    assert before_follow["isFollowing"] is False

    follow_query = """
        mutation Follow($username: String!) {
          follow(username: $username) { following followers followingCount }
        }
    """
    follow = assert_graphql_success(graphql(authenticated, follow_query, {"username": target_username}))["follow"]
    assert follow["following"] is True
    assert follow["followers"] == 1
    assert follow["followingCount"] == 1
    after_follow = assert_graphql_success(graphql(
        authenticated, public_profile_query, {"username": target_username}
    ))["profile"]
    assert after_follow["followers"] == 1
    assert after_follow["isFollowing"] is True

    duplicate_follow = assert_graphql_success(graphql(
        authenticated, follow_query, {"username": target_username}
    ))["follow"]
    assert duplicate_follow == {"following": True, "followers": 1, "followingCount": 1}

    following = assert_graphql_success(graphql(
        authenticated, "query { myFollowing { username } }"
    ))["myFollowing"]
    assert [profile["username"] for profile in following].count(target_username) == 1

    following_page_query = """
        query { myFollowingPage(limit: 1) {
          profiles { username }
          nextCursor
        } }
    """
    following_page = assert_graphql_success(graphql(
        authenticated, following_page_query
    ))["myFollowingPage"]
    assert [profile["username"] for profile in following_page["profiles"]] == [target_username]

    unfollow_query = """
        mutation Unfollow($username: String!) {
          unfollow(username: $username) { following followers followingCount }
        }
    """
    unfollow = assert_graphql_success(graphql(authenticated, unfollow_query, {"username": target_username}))["unfollow"]
    assert unfollow["following"] is False
    assert unfollow["followers"] == 0
    assert unfollow["followingCount"] == 0
    after_unfollow = assert_graphql_success(graphql(
        authenticated, public_profile_query, {"username": target_username}
    ))["profile"]
    assert after_unfollow["followers"] == 0
    assert after_unfollow["isFollowing"] is False

    duplicate_unfollow = assert_graphql_success(graphql(
        authenticated, unfollow_query, {"username": target_username}
    ))["unfollow"]
    assert duplicate_unfollow == {"following": False, "followers": 0, "followingCount": 0}

    print("6. Delete account")
    deleted = request_json(authenticated, "/auth/delete-account", {})
    assert deleted["ok"] is True

    after_delete_me = graphql(authenticated, me_query)
    assert after_delete_me["data"]["me"] is None

    login_after_delete = request_json(anonymous, "/auth/login", {
        "email": email,
        "password": password,
    }, expected_status=401)
    assert login_after_delete.get("detail") == "Invalid credentials"

    deleted_profile = assert_graphql_success(graphql(
        anonymous, public_profile_query, {"username": username}
    ))["profile"]
    assert deleted_profile is None

    print("7. Reject protected requests")

    protected_update = graphql(anonymous, update_query, {"input": {"bio": "must fail"}})
    assert protected_update.get("errors"), protected_update
    assert protected_update["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"

    protected_follow = graphql(anonymous, follow_query, {"username": "luna"})
    assert protected_follow.get("errors"), protected_follow

    print("8. Reject duplicate email and username")
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
