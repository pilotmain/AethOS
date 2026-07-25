/** Phase 4 operator surfaces API. */

import { apiBase } from "@/lib/api";

export async function fetchResearchNotes(sessionId?: string) {
  const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  const res = await fetch(`${apiBase()}/api/v1/research/notes${qs}`, { cache: "no-store" });
  if (!res.ok) return { ok: false, notes: [] as Record<string, unknown>[] };
  return res.json() as Promise<{ ok: boolean; notes: Record<string, unknown>[] }>;
}

export async function pinResearchNote(
  sessionId: string,
  body: { text: string; replay_id?: string; query?: string },
) {
  const res = await fetch(`${apiBase()}/api/v1/research/notes/${encodeURIComponent(sessionId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function runBlindEval(
  prompt: string,
  modelA?: string | null,
  modelB?: string | null,
) {
  const res = await fetch(`${apiBase()}/api/v1/research/blind-eval`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ prompt, model_a: modelA ?? null, model_b: modelB ?? null }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function fetchToolPolicyMatrix() {
  const res = await fetch(`${apiBase()}/api/v1/runtime/agent-tool-policy/matrix`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json() as Promise<{ channels?: Record<string, unknown>[] }>;
}

export async function fetchCronStatus() {
  const res = await fetch(`${apiBase()}/api/v1/runtime/cron/status`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function fetchSandboxStatus() {
  const res = await fetch(`${apiBase()}/api/v1/runtime/sandbox/status`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function proposeSandboxProbe(command: string, sessionId = "operator") {
  const res = await fetch(`${apiBase()}/api/v1/runtime/sandbox/probe`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ command, session_id: sessionId }),
  });
  return res.json();
}

export async function fetchDeliveryStatus() {
  const res = await fetch(`${apiBase()}/api/v1/delivery/status`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

// ── Multi-model arbiter ──────────────────────────────────────────────────────

export interface ArbiterModelResponse {
  model_label: string;
  response_id: string;
  text_preview: string | null;
  latency_ms: number;
  error: string | null;
}

export interface ArbiterConsensus {
  reached: boolean;
  agreement_score: number;
  winning_model: string | null;
  winning_text: string | null;
  summary: string;
  agreeing_models: number;
  dissenting_model_ids: string[];
}

export interface ArbiterCritiqueRow {
  critic: string;
  target: string;
  overall_score: number;
  accuracy_score: number;
  completeness_score: number;
  reasoning_score: number;
  recommended: boolean;
  critique: string;
}

export interface ArbiterDebateRound {
  round: number;
  agreement_score: number;
  consensus_reached: boolean;
  winning_model: string | null;
  answers: { model_label: string; text_preview: string }[];
}

export interface ArbiterSessionResult {
  status: string;
  consensus: ArbiterConsensus | null;
  responses: ArbiterModelResponse[];
  critiques?: ArbiterCritiqueRow[];
  debate_rounds?: ArbiterDebateRound[];
  rounds_completed?: number;
}

export interface ArbiterAvailableModel {
  provider: string;
  model_id: string;
  label: string;
  pool_id: string;
}

export interface ArbiterStatus {
  enabled: boolean;
  pool: { provider: string; model_id: string; label: string }[];
  pool_valid: boolean;
  pool_errors: string[];
  available_models: ArbiterAvailableModel[];
  pool_source: "explicit" | "connected_models_default";
  config: {
    consensus_threshold: number;
    max_rounds: number;
    max_models: number;
    blind_critique: boolean;
    timeout_sec: number;
  };
}

/** Check arbiter config and pool validity. */
export async function fetchArbiterStatus(): Promise<ArbiterStatus | null> {
  const res = await fetch(`${apiBase()}/api/v1/arbiter/status`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json() as Promise<ArbiterStatus>;
}

/**
 * Start an arbiter session and wait for completion. The backend runs
 * dispatch → critique → consensus synchronously in the POST response; we then
 * read the terminal consensus payload (polling defensively for slow pools).
 */
export async function runArbiterSession(
  prompt: string,
  sessionId = "mission-control",
  debateRounds = 0,
): Promise<ArbiterSessionResult | null> {
  // Start in the background and poll — a multi-round, multi-model debate runs for
  // minutes, which would otherwise 502 a single synchronous request at the gateway.
  const res = await fetch(`${apiBase()}/api/v1/arbiter/sessions/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ prompt, session_id: sessionId, debate_rounds: debateRounds }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Arbiter request failed (${res.status})`);
  }
  const start = (await res.json()) as {
    arbiter_session_id: string;
    status: string;
    message: string;
  };

  // ~6 min budget: dispatch + critique + debate rounds across several models.
  for (let i = 0; i < 180; i++) {
    const poll = await fetch(
      `${apiBase()}/api/v1/arbiter/sessions/${encodeURIComponent(start.arbiter_session_id)}/consensus`,
      { cache: "no-store" },
    );
    if (poll.ok) {
      const data = (await poll.json()) as ArbiterSessionResult & { status: string };
      if (!["pending", "dispatching", "critiquing"].includes(data.status)) {
        return data;
      }
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  return null;
}

/** Load the full judgment (consensus + responses + critique scorecard + debate) for
 * one past session — powers the clickable history so results are always findable. */
export async function fetchArbiterConsensus(
  sessionId: string,
): Promise<ArbiterSessionResult | null> {
  const res = await fetch(
    `${apiBase()}/api/v1/arbiter/sessions/${encodeURIComponent(sessionId)}/consensus`,
    { cache: "no-store" },
  );
  if (!res.ok) return null;
  return res.json() as Promise<ArbiterSessionResult>;
}

/** List recent arbiter sessions (for the history view). */
export async function fetchArbiterSessions(
  limit = 10,
): Promise<{ sessions: Record<string, unknown>[] }> {
  const res = await fetch(`${apiBase()}/api/v1/arbiter/sessions?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) return { sessions: [] };
  return res.json() as Promise<{ sessions: Record<string, unknown>[] }>;
}
