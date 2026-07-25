/** Server-persisted chat threads API. */

import { apiBase, apiFetch } from "@/lib/api";
import type { CachedMessage } from "@/lib/chat/types";

export type ServerThreadSummary = {
  session_id: string;
  title: string;
  created_at?: number;
  updated_at?: number;
  message_count?: number;
};

export type ServerThreadDetail = {
  session_id: string;
  title: string;
  messages: CachedMessage[];
  created_at?: number;
  updated_at?: number;
};

export async function fetchServerThreadList(): Promise<ServerThreadSummary[]> {
  const res = await apiFetch(`${apiBase()}/api/v1/chat/threads`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return [];
  const data = (await res.json()) as { threads?: ServerThreadSummary[] };
  return data.threads ?? [];
}

export async function fetchServerThread(sessionId: string): Promise<ServerThreadDetail | null> {
  const sid = encodeURIComponent(sessionId);
  const res = await apiFetch(`${apiBase()}/api/v1/chat/threads/${sid}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { thread?: ServerThreadDetail };
  return data.thread ?? null;
}

export async function upsertServerThread(
  sessionId: string,
  title: string,
  messages: CachedMessage[],
): Promise<boolean> {
  const sid = encodeURIComponent(sessionId);
  const res = await apiFetch(`${apiBase()}/api/v1/chat/threads/${sid}`, {
    method: "PUT",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ title, messages }),
  });
  return res.ok;
}

export async function createServerThread(sessionId: string, title: string): Promise<boolean> {
  const res = await apiFetch(`${apiBase()}/api/v1/chat/threads`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, title }),
  });
  return res.ok;
}

export async function deleteServerThread(sessionId: string): Promise<boolean> {
  const sid = encodeURIComponent(sessionId);
  const res = await apiFetch(`${apiBase()}/api/v1/chat/threads/${sid}`, { method: "DELETE" });
  return res.ok;
}
