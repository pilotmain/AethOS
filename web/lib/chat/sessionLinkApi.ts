/** Session alias linking — Telegram ↔ web continuity. */

import { apiBase } from "@/lib/api";

export type SessionGroup = {
  ok?: boolean;
  canonical_session_id?: string;
  session_id?: string;
  linked_session_ids?: string[];
};

export async function fetchSessionGroup(sessionId: string): Promise<SessionGroup | null> {
  const sid = encodeURIComponent(sessionId);
  const res = await fetch(`${apiBase()}/api/v1/runtime/sessions/${sid}/group`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return null;
  return res.json() as Promise<SessionGroup>;
}

export async function linkSessionIds(
  sessionIds: string[],
  canonicalSessionId?: string,
): Promise<SessionGroup | null> {
  const res = await fetch(`${apiBase()}/api/v1/runtime/sessions/link`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      session_ids: sessionIds,
      canonical_session_id: canonicalSessionId || undefined,
    }),
  });
  if (!res.ok) return null;
  return res.json() as Promise<SessionGroup>;
}
