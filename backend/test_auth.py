#!/usr/bin/env python3
"""Test script for auth endpoints."""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8002"

def test_register():
    """Test user registration."""
    print("Testing registration...")
    payload = {
        "email": "test@connextionz.app",
        "password": "testpass123",
        "username": "testuser",
        "display_name": "Test User",
    }
    req = urllib.request.Request(
        f"{BASE_URL}/auth/register",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            print(f"Registration result: {json.dumps(result, indent=2)}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Registration error ({e.code}): {error_body}")
        return None

def test_login():
    """Test user login."""
    print("\nTesting login...")
    payload = {
        "email": "demo@connextionz.app",
        "password": "demo",  # Matches seed data
    }
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            print(f"Login result: {json.dumps(result, indent=2)}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Login error ({e.code}): {error_body}")
        return None

def test_me_query_unauthenticated():
    """Test me query without auth."""
    print("\nTesting me query (unauthenticated)...")
    payload = {
        "query": "query { me { username displayName bio } }"
    }
    req = urllib.request.Request(
        f"{BASE_URL}/graphql",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            print(f"Me query result: {json.dumps(result, indent=2)}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Me query error ({e.code}): {error_body}")
        return None

if __name__ == "__main__":
    print("=== Auth Flow Tests ===\n")
    
    # First, try to login with existing user (or register if needed)
    login_result = test_login()
    if not login_result or not login_result.get("ok"):
        print("\nExisting user not found, registering...")
        reg_result = test_register()
        if reg_result and reg_result.get("ok"):
            print("Registration succeeded, trying login again...")
            login_result = test_login()
    
    # Test me query without cookies
    test_me_query_unauthenticated()
    
    print("\n=== End of Tests ===")
