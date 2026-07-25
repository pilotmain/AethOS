/** Mission Control API fetch — legacy route probe + 404 suppression. */

import { apiBase } from "@/lib/api";
import { assertNoLegacyProbe, fetchWithRouteProbe } from "@/lib/api/routeProbe";

export async function mcFetch<T>(path: string, init?: RequestInit): Promise<T> {
  assertNoLegacyProbe(path);
  const res = await fetchWithRouteProbe(`${apiBase()}${path}`, {
    cache: "no-store",
    credentials: "include",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}
