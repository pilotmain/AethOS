import { apiBase, apiFetch } from "@/lib/api";

export type ModelCatalogEntry = {
  id: string;
  provider: string;
  model: string;
  label: string;
  configured: boolean;
  agent_tool_capable?: boolean;
};

export type ModelCatalogSnapshot = {
  ok: boolean;
  models: ModelCatalogEntry[];
  default_catalog_id: string;
  env_default: ModelCatalogEntry;
  session_override: string | null;
  effective: {
    catalog_id: string;
    provider: string;
    model: string;
    label: string;
    source: string;
  };
};

const STORAGE_PREFIX = "aethos_session_model_override:";

export function readSessionModelOverride(sessionId: string): string | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(`${STORAGE_PREFIX}${sessionId}`);
  return raw && raw.trim() ? raw.trim() : null;
}

export function writeSessionModelOverride(sessionId: string, catalogId: string | null): void {
  if (typeof window === "undefined") return;
  const key = `${STORAGE_PREFIX}${sessionId}`;
  if (!catalogId || catalogId === "default") {
    localStorage.removeItem(key);
    return;
  }
  localStorage.setItem(key, catalogId);
}

export async function fetchModelCatalog(sessionId: string): Promise<ModelCatalogSnapshot> {
  const qs = new URLSearchParams({ session_id: sessionId });
  const res = await apiFetch(`${apiBase()}/api/v1/runtime/models?${qs.toString()}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Model catalog failed (${res.status})`);
  }
  return res.json();
}

export async function persistSessionModelOverride(
  sessionId: string,
  catalogId: string | null,
): Promise<ModelCatalogSnapshot["effective"]> {
  const res = await apiFetch(`${apiBase()}/api/v1/runtime/sessions/${encodeURIComponent(sessionId)}/model-override`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ catalog_id: catalogId }),
  });
  if (!res.ok) {
    throw new Error(`Model override save failed (${res.status})`);
  }
  const body = (await res.json()) as { effective?: ModelCatalogSnapshot["effective"] };
  writeSessionModelOverride(sessionId, catalogId);
  if (!body.effective) {
    throw new Error("Model override response missing effective model");
  }
  return body.effective;
}

export function modelPickerLabel(entry: ModelCatalogEntry | undefined, fallback = "Default (.env)"): string {
  if (!entry) return fallback;
  return entry.label || entry.model || fallback;
}

export type UsageCost = { usd: number | null; known: boolean; label: string };
export type UsageTokens = { input: number; output: number; total: number };
export type UsageContext = {
  used: number | null;
  limit: number | null;
  pct: number | null;
  known: boolean;
};
export type UsageCache = {
  read_tokens: number;
  creation_tokens: number;
  hit_ratio: number | null;
  known: boolean;
};

export type UsageModelBreakdown = {
  model: string;
  provider: string | null;
  tokens: UsageTokens;
  cost: UsageCost;
  turns: number;
  pct: number;
};

export type SessionUsage = {
  ok: boolean;
  model: string | null;
  provider: string | null;
  tokens: UsageTokens;
  cost: UsageCost;
  context?: UsageContext;
  cache?: UsageCache;
  turns: number;
  session: {
    session_id: string;
    model: string | null;
    provider: string | null;
    tokens: UsageTokens;
    cost: UsageCost;
    context?: UsageContext;
    cache?: UsageCache;
    turns: number;
    models?: UsageModelBreakdown[];
  } | null;
};

/** Honest, always-visible usage for the chat header strip. Never throws. */
export async function fetchSessionUsage(sessionId: string): Promise<SessionUsage | null> {
  try {
    const qs = new URLSearchParams({ session_id: sessionId });
    const res = await apiFetch(`${apiBase()}/api/v1/observability/metering?${qs.toString()}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return (await res.json()) as SessionUsage;
  } catch {
    return null;
  }
}
