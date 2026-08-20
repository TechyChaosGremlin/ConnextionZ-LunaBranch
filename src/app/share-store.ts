import { useCallback, useState, useSyncExternalStore } from "react";
import { type Result } from "./auth-store";
import { sharePost } from "./profile-graphql";

let counts = new Map<string, number>();
let shared = new Map<string, boolean>();
let pending = new Set<string>();
let activeEmail: string | null = null;

const listeners = new Set<() => void>();

function publish() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function activateShareGraph(email: string | null) {
  const normalizedEmail = email?.trim().toLowerCase() ?? null;
  if (activeEmail === normalizedEmail) return;
  activeEmail = normalizedEmail;
  counts = new Map();
  shared = new Map();
  pending = new Set();
  publish();
}

export function noteShareState(postId: string, shares: number, isShared = false) {
  if (counts.has(postId)) return;
  counts = new Map(counts).set(postId, shares);
  shared = new Map(shared).set(postId, isShared);
  publish();
}

export async function recordShare(postId: string): Promise<Result<number>> {
  if (pending.has(postId)) return { ok: false, error: "" };

  const previousCount = counts.get(postId) ?? 0;
  const previousShared = shared.get(postId) ?? false;
  counts = new Map(counts).set(postId, previousCount + 1);
  shared = new Map(shared).set(postId, true);
  pending = new Set(pending).add(postId);
  publish();

  const result = await sharePost(postId);
  pending = new Set(pending);
  pending.delete(postId);

  if (!result.ok) {
    counts = new Map(counts).set(postId, previousCount);
    shared = new Map(shared).set(postId, previousShared);
    publish();
    return result;
  }

  counts = new Map(counts).set(postId, result.value.shares);
  shared = new Map(shared).set(postId, result.value.shared);
  publish();
  return { ok: true, value: result.value.shares };
}

export function useShare(postId: string, fallbackShares: number) {
  const shareCount = useSyncExternalStore(subscribe, () => counts.get(postId) ?? fallbackShares);
  const isShared = useSyncExternalStore(subscribe, () => shared.get(postId) ?? false);
  const isPending = useSyncExternalStore(subscribe, () => pending.has(postId));
  const [error, setError] = useState("");

  const share = useCallback(async () => {
    setError("");
    const result = await recordShare(postId);
    if (!result.ok && result.error) {
      setError(result.error);
      setTimeout(() => setError(""), 2600);
    }
    return result;
  }, [postId]);

  return { shares: shareCount, isShared, pending: isPending, error, share };
}