// ─── SAVE STORE ──────────────────────────────────────────────────────────────
//
// Per-post save (bookmark) state for the signed-in viewer. Mirrors the like
// store: posts arrive carrying their own `isSaved` and `saves`, so the store is
// seeded incrementally through `noteSaveState` rather than loaded up front.
//
// Writes are optimistic: the bookmark and the count flip before the request
// resolves; a failure rolls both back.

import { useCallback, useState, useSyncExternalStore } from "react";
import { type Result } from "./auth-store";
import { savePost, unsavePost } from "./profile-graphql";

let saved = new Map<string, boolean>();
let counts = new Map<string, number>();
let pending = new Set<string>();
let activeEmail: string | null = null;

const listeners = new Set<() => void>();

function publish() {
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function activateSaveGraph(email: string | null) {
  const normalizedEmail = email?.trim().toLowerCase() ?? null;
  if (activeEmail === normalizedEmail) return;
  activeEmail = normalizedEmail;
  saved = new Map();
  counts = new Map();
  pending = new Set();
  publish();
}

/**
 * Folds a post's server-known save state into the store. A no-op once the post
 * has been seen before, so a later page or refetch can never clobber an
 * in-flight or already-resolved toggle with a stale snapshot.
 */
export function noteSaveState(postId: string, isSaved: boolean, saves: number) {
  if (saved.has(postId)) return;
  saved = new Map(saved).set(postId, isSaved);
  counts = new Map(counts).set(postId, saves);
  publish();
}

/** The network seam. Resolves once the save/unsave is durable. */
async function requestSave(postId: string, next: boolean): Promise<Result<{ saved: boolean; saves: number }>> {
  return next ? savePost(postId) : unsavePost(postId);
}

/**
 * Applies the toggle immediately, then confirms it. Returns the error to show
 * next to the button when the write failed and the state was rolled back.
 */
export async function toggleSave(postId: string): Promise<Result<boolean>> {
  if (pending.has(postId)) return { ok: false, error: "" };

  const previousSaved = saved.get(postId) ?? false;
  const previousCount = counts.get(postId) ?? 0;
  const next = !previousSaved;

  saved = new Map(saved).set(postId, next);
  counts = new Map(counts).set(postId, Math.max(0, previousCount + (next ? 1 : -1)));
  pending = new Set(pending).add(postId);
  publish();

  const result = await requestSave(postId, next);

  pending = new Set(pending);
  pending.delete(postId);

  if (!result.ok) {
    saved = new Map(saved).set(postId, previousSaved);
    counts = new Map(counts).set(postId, previousCount);
    publish();
    return result;
  }

  // The server's own numbers are authoritative — apply them now instead of
  // trusting the optimistic +/-1.
  saved = new Map(saved).set(postId, result.value.saved);
  counts = new Map(counts).set(postId, result.value.saves);
  publish();
  return { ok: true, value: result.value.saved };
}

/**
 * Everything a save button needs. `fallbackSaved`/`fallbackSaves` are the
 * values carried on the post itself, used until (and unless) the store has been
 * seeded or the viewer has toggled it.
 */
export function useSave(postId: string, fallbackSaved: boolean, fallbackSaves: number) {
  const isSaved = useSyncExternalStore(subscribe, () => saved.get(postId) ?? fallbackSaved);
  const saveCount = useSyncExternalStore(subscribe, () => counts.get(postId) ?? fallbackSaves);
  const isPending = useSyncExternalStore(subscribe, () => pending.has(postId));
  const [error, setError] = useState("");

  const toggle = useCallback(async () => {
    setError("");
    const result = await toggleSave(postId);
    // An empty error means "already in flight" — not something to report.
    if (!result.ok && result.error) {
      setError(result.error);
      setTimeout(() => setError(""), 2600);
    }
  }, [postId]);

  return { saved: isSaved, saves: saveCount, pending: isPending, error, toggle };
}
