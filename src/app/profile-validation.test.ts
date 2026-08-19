import test from "node:test";
import assert from "node:assert/strict";

import { normalizeProfilePatch, validateProfilePatch } from "./profile-validation.ts";

test("requires a valid username pattern", () => {
  assert.deepEqual(validateProfilePatch({ username: "ab" }), {
    username: "Usernames are 3–24 characters: letters, numbers, dots and underscores.",
  });
});

test("accepts a valid website with a scheme and rejects malformed values", () => {
  assert.deepEqual(validateProfilePatch({ website: "https://example.com" }), {});
  assert.deepEqual(validateProfilePatch({ website: "not-a-url" }), {
    website: "Enter a valid website URL, like https://example.com.",
  });
});

test("rejects arbitrary avatar URL edits", () => {
  assert.deepEqual(validateProfilePatch({ avatarUrl: "https://cdn.example.com/avatar.png" }), {});
  assert.deepEqual(validateProfilePatch({ avatarUrl: "javascript:alert(1)" }), {
    avatarUrl: "Profile photos can only be uploaded from your device or kept as-is.",
  });
});

test("normalizes display name, bio, website and avatar URL", () => {
  assert.deepEqual(normalizeProfilePatch({
    displayName: "  Maya    Chen  ",
    bio: "  Producer and visual creator.  ",
    website: "example.com",
    avatarUrl: "  https://cdn.example.com/avatar.png  ",
  }), {
    displayName: "Maya Chen",
    bio: "Producer and visual creator.",
    website: "https://example.com",
    avatarUrl: "https://cdn.example.com/avatar.png",
  });
});

test("rejects empty display names after normalization", () => {
  assert.deepEqual(validateProfilePatch({ displayName: "    " }), {
    displayName: "Display name cannot be empty.",
  });
});
