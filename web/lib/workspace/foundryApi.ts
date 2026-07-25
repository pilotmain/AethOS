/** Workspace suite — Model Foundry API (handoff §8). Serve is governed; loopback only. */

import { apiBase, apiFetch } from "@/lib/api";

export type Hardware = {
  ok: boolean;
  error?: string;
  system?: string;
  arch?: string;
  cpu_count?: number;
  detection_unavailable?: boolean;
  total_ram_gb?: number | null;
  unified_memory?: boolean;
  usable_vram_gb?: number | null;
};

export type ModelFit = {
  id: string;
  label: string;
  params_b: number;
  min_gb: number;
  quant: string;
  fit_score: number;
  fits: boolean;
  verdict: "great" | "ok" | "tight" | "no";
};

export type RecommendResponse = {
  ok: boolean;
  error?: string;
  hardware?: Hardware;
  detection_unavailable?: boolean;
  model_count?: number;
  models: ModelFit[];
};

const base = () => `${apiBase()}/api/v1/human/workspace/foundry`;

export async function scanHardware(): Promise<Hardware> {
  const res = await apiFetch(`${base()}/scan`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function recommendModels(): Promise<RecommendResponse> {
  const res = await apiFetch(`${base()}/recommend`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}`, models: [] };
  return res.json();
}

export async function serveModelPreflight(
  modelId: string,
  port = 11434,
): Promise<{ ok: boolean; error?: string; note?: string; serve_request?: ServeRequest }> {
  const res = await apiFetch(`${base()}/serve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ model_id: modelId, port }),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export type ServeStatus =
  | "pending_approval"
  | "preflight"
  | "starting"
  | "downloading"
  | "served"
  | "stopped";

export type ServeRequest = {
  id: string;
  model_id: string;
  label?: string;
  status?: ServeStatus;
  phase?: string;
  progress?: number;
  error?: string;
  executed?: boolean;
  bind?: string;
  port?: number;
  endpoint?: string;
  created_at?: number;
  served_at?: number;
  stopped_at?: number;
};

export type ServeStatusResponse = {
  ok: boolean;
  error?: string;
  serve_requests: ServeRequest[];
  autostart_enabled?: boolean;
  autodownload_enabled?: boolean;
};

export async function serveStatus(): Promise<ServeStatusResponse> {
  const res = await apiFetch(`${base()}/serve-status`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}`, serve_requests: [] };
  return res.json();
}

export async function stopServe(id: string): Promise<{ ok: boolean; error?: string; note?: string }> {
  const res = await apiFetch(`${base()}/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ id }),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function dismissServeRequest(
  id: string,
): Promise<{ ok: boolean; error?: string; dismissed?: string }> {
  const res = await apiFetch(`${base()}/dismiss`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ id }),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}
