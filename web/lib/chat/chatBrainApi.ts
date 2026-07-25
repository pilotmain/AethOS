/** Chat Brain panel — vector memory + research session continuity. */

import { apiBase } from "@/lib/api";

export type VectorMemorySnapshot = {
  ok: boolean;
  enabled: boolean;
  backend: string;
  entry_count: number;
  recent: { id?: string; text?: string; tags?: string[]; environment?: string }[];
};

export type ResearchSessionMemory = {
  replay_id?: string;
  query?: string;
  comparison?: boolean;
  subjects?: string[] | null;
  updated_at?: number;
};

export type MemoryRecallMatch = {
  id?: string;
  text?: string;
  score?: number;
  tags?: string[];
  environment?: string;
};

export type MemoryRecallResult = {
  ok: boolean;
  error?: string;
  backend?: string;
  matches?: MemoryRecallMatch[];
};

export type ChatBrainContext = {
  memory: VectorMemorySnapshot | null;
  research: ResearchSessionMemory | null;
};

export async function fetchVectorMemorySnapshot(limit = 5): Promise<VectorMemorySnapshot | null> {
  const res = await fetch(`${apiBase()}/api/v1/runtime/memory/snapshot?limit=${limit}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return null;
  return res.json() as Promise<VectorMemorySnapshot>;
}

export async function fetchResearchSessionMemory(sessionId: string): Promise<ResearchSessionMemory | null> {
  const sid = encodeURIComponent(sessionId || "default");
  const res = await fetch(`${apiBase()}/api/v1/research/session-memory/${sid}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { memory?: ResearchSessionMemory | null };
  return data.memory ?? null;
}

export async function fetchMemoryRecall(query: string, limit = 5): Promise<MemoryRecallResult> {
  const q = query.trim();
  if (!q) return { ok: false, error: "query_required", matches: [] };
  const res = await fetch(`${apiBase()}/api/v1/runtime/memory/recall`, {
    method: "POST",
    cache: "no-store",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ query: q, limit }),
  });
  if (!res.ok) return { ok: false, error: `recall_failed_${res.status}`, matches: [] };
  return res.json() as Promise<MemoryRecallResult>;
}

export async function fetchChatBrainContext(sessionId: string): Promise<ChatBrainContext> {
  const [memory, research] = await Promise.all([
    fetchVectorMemorySnapshot(5),
    fetchResearchSessionMemory(sessionId),
  ]);
  return { memory, research };
}
