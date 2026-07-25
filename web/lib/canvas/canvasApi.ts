/** Live Canvas read-only state API (handoff §11). Render surface only. */

import { apiBase, apiFetch } from "@/lib/api";
import { swrFetch } from "@/lib/clientDataCache";

export type CanvasView = {
  id: string;
  view_type: "status" | "diff" | "research_report" | "job_timeline" | "table" | "markdown";
  title: string;
  data?: unknown;
  read_only?: boolean;
  created_at?: number;
};

export type CanvasState = {
  ok: boolean;
  session_id?: string;
  /** Session the returned views actually came from (may differ from the requested
   * session when the backend fell back to the tenant's most recent render). */
  resolved_session?: string;
  /** True when views are the tenant's latest render from a different session. */
  showing_latest_render?: boolean;
  read_only?: boolean;
  view_count?: number;
  views: CanvasView[];
};

async function fetchCanvasStateRaw(sessionId: string, limit = 20): Promise<CanvasState> {
  const sid = encodeURIComponent(sessionId || "default");
  const res = await apiFetch(`${apiBase()}/api/v1/human/canvas/${sid}?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    return { ok: false, views: [] };
  }
  return res.json() as Promise<CanvasState>;
}

export async function fetchCanvasState(
  sessionId: string,
  limit = 20,
  opts?: { revalidate?: (state: CanvasState) => void },
): Promise<CanvasState> {
  const key = `canvas:${sessionId || "default"}:${limit}`;
  return swrFetch(key, () => fetchCanvasStateRaw(sessionId, limit), {
    ttlMs: 8_000,
    onRevalidate: opts?.revalidate,
  });
}
