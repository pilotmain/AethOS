/** Lightweight stale-while-revalidate cache keyed by tenant + route. */

import { getActiveUserScope } from "@/lib/auth/userScope";

type CacheEntry<T> = {
  data: T;
  at: number;
  ttlMs: number;
};

const store = new Map<string, CacheEntry<unknown>>();

function scopedKey(key: string): string {
  return `${getActiveUserScope()}:${key}`;
}

export function readCached<T>(key: string): T | null {
  const row = store.get(scopedKey(key)) as CacheEntry<T> | undefined;
  if (!row) return null;
  if (Date.now() - row.at > row.ttlMs) {
    store.delete(scopedKey(key));
    return null;
  }
  return row.data;
}

export function writeCached<T>(key: string, data: T, ttlMs = 30_000): void {
  store.set(scopedKey(key), { data, at: Date.now(), ttlMs });
}

export function invalidateCached(key: string): void {
  store.delete(scopedKey(key));
}

/** Return cached data immediately when fresh; always revalidate in the background. */
export async function swrFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  opts?: { ttlMs?: number; onRevalidate?: (data: T) => void },
): Promise<T> {
  const ttlMs = opts?.ttlMs ?? 30_000;
  const cached = readCached<T>(key);
  if (cached !== null) {
    void fetcher()
      .then((fresh) => {
        writeCached(key, fresh, ttlMs);
        opts?.onRevalidate?.(fresh);
      })
      .catch(() => {
        /* keep stale */
      });
    return cached;
  }
  const data = await fetcher();
  writeCached(key, data, ttlMs);
  return data;
}
