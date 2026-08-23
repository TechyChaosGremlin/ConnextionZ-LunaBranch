#!/usr/bin/env python3
"""Verify session cookies, protected GraphQL mutations, and logout."""

import json
import urllib.request

BASE_URL = "http://127.0.0.1:8002"
LOGIN = {"email": "demo@connextionz.app", "password": "demo"}


def request_json(opener, path, payload, method="POST"):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with opener.open(request, timeout=10) as response:
        return json.loads(response.read().decode()), response.headers


def graphql(opener, query, variables=None):
    return request_json(opener, "/graphql", {"query": query, "variables": variables or {}})


def main():
    anonymous = urllib.request.build_opener()
    protected_mutation = """
        mutation UpdateProfile($input: UpdateProfileInput!) {
          updateProfile(input: $input) { username }
        }
    """
    result, _ = graphql(anonymous, protected_mutation, {"input": {"bio": "should be rejected"}})
    assert result.get("errors"), "Unauthenticated profile mutation unexpectedly succeeded"

    cookies = urllib.request.HTTPCookieProcessor()
    authenticated = urllib.request.build_opener(cookies)
    login_result, login_headers = request_json(authenticated, "/auth/login", LOGIN)
    assert login_result.get("ok") is True, f"Login failed: {login_result}"
    set_cookie = login_headers.get("Set-Cookie", "")
    assert "connextionz_session=" in set_cookie, f"Session cookie missing: {set_cookie}"
    assert "httponly" in set_cookie.lower(), f"Session cookie is not HttpOnly: {set_cookie}"

    me_query = "query { me { username displayName } }"
    me_result, _ = graphql(authenticated, me_query)
    assert me_result.get("data", {}).get("me", {}).get("username") == "luna", me_result

    authenticated_result, _ = graphql(
        authenticated,
        protected_mutation,
        {"input": {"displayName": "Luna Hart"}},
    )
    assert not authenticated_result.get("errors"), authenticated_result

    logout_result, _ = request_json(authenticated, "/auth/logout", {})
    assert logout_result.get("ok") is True, logout_result

    after_logout, _ = graphql(authenticated, me_query)
    assert after_logout.get("data", {}).get("me") is None, after_logout

    print("SESSION_TESTS_PASSED")


if __name__ == "__main__":
    main()
