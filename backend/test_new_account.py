#!/usr/bin/env python3
"""Test registration and login flow for new accounts."""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8002"

def register_new_account():
    """Register a new test account."""
    print("=" * 60)
    print("REGISTERING NEW ACCOUNT")
    print("=" * 60)
    
    payload = {
        "email": "alex.creates@connextionz.app",
        "password": "testpass123",
        "username": "alex.creates",
        "display_name": "Alex Creates",
    }
    
    print(f"\nRequest: POST /auth/register")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    req = urllib.request.Request(
        f"{BASE_URL}/auth/register",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            print(f"\nResponse: {result['ok']}")
            print(f"User ID: {result['user']['id']}")
            print(f"Email: {result['user']['email']}")
            print(f"Profile: {result['profile']}")
            return result
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode())
        print(f"\nError ({e.code}): {error_body}")
        return None

def login_with_new_account():
    """Login with the newly created account."""
    print("\n" + "=" * 60)
    print("LOGIN WITH NEW ACCOUNT")
    print("=" * 60)
    
    payload = {
        "email": "alex.creates@connextionz.app",
        "password": "testpass123",
    }
    
    print(f"\nRequest: POST /auth/login")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            print(f"\nResponse: {result['ok']}")
            print(f"User ID: {result['user']['id']}")
            print(f"Email: {result['user']['email']}")
            print(f"Profile: {result['profile']}")
            return result
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode())
        print(f"\nError ({e.code}): {error_body}")
        return None

def query_profile_via_graphql(username: str):
    """Query the new user's profile via GraphQL."""
    print("\n" + "=" * 60)
    print(f"QUERY PROFILE VIA GRAPHQL: {username}")
    print("=" * 60)
    
    payload = {
        "query": f"""
        query {{
          profile(username: "{username}") {{
            id
            username
            displayName
            bio
            location
            website
            verified
            avatarColor
            collabStatus
            collabScore
            followers
            following
          }}
        }}
        """
    }
    
    print(f"\nRequest: POST /graphql")
    print(f"Query: profile(username: \"{username}\")")
    
    req = urllib.request.Request(
        f"{BASE_URL}/graphql",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            if result.get("errors"):
                print(f"\nGraphQL Errors: {result['errors']}")
                return None
            
            profile = result.get("data", {}).get("profile")
            print(f"\nResponse: Found profile")
            print(f"Profile: {json.dumps(profile, indent=2)}")
            return profile
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"\nError ({e.code}): {error_body}")
        return None

def test_duplicate_registration():
    """Test that registering with the same email fails."""
    print("\n" + "=" * 60)
    print("TEST DUPLICATE EMAIL REJECTION")
    print("=" * 60)
    
    payload = {
        "email": "alex.creates@connextionz.app",
        "password": "different_password",
        "username": "alex_duplicate",
        "display_name": "Alex Duplicate",
    }
    
    print(f"\nRequest: POST /auth/register (duplicate email)")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    req = urllib.request.Request(
        f"{BASE_URL}/auth/register",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            print(f"\nUnexpected success: {result}")
            return False
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode())
        if e.code == 409:
            print(f"\nExpected error ({e.code}): {error_body['detail']}")
            return True
        print(f"\nUnexpected error ({e.code}): {error_body}")
        return False

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " NEW ACCOUNT REGISTRATION & LOGIN TEST ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Test 1: Register new account
    reg_result = register_new_account()
    if not reg_result or not reg_result.get("ok"):
        print("\n❌ Registration failed!")
        exit(1)
    
    # Test 2: Login with new account
    login_result = login_with_new_account()
    if not login_result or not login_result.get("ok"):
        print("\n❌ Login failed!")
        exit(1)
    
    # Test 3: Query profile via GraphQL
    username = reg_result["profile"]["username"]
    profile_result = query_profile_via_graphql(username)
    if not profile_result:
        print("\n❌ GraphQL query failed!")
        exit(1)
    
    # Test 4: Try registering with same email again
    dup_result = test_duplicate_registration()
    if not dup_result:
        print("\n❌ Duplicate email check failed!")
        exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nNew account created and verified:")
    print(f"  Email: alex.creates@connextionz.app")
    print(f"  Username: {username}")
    print(f"  Display Name: {reg_result['profile']['displayName']}")
    print(f"\nYou can now test this account in the web app!")
    print()
