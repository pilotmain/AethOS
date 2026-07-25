/** Reliability runtime — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ReliabilityTruth = {
  truth_state?: string;
  executed?: boolean;
  verified?: boolean;
  confidence?: string;
  bounded_confidence?: number;
  summary?: string;
};

export type ReliabilityScores = {
  global_reliability_score?: number;
  trust_level?: string;
  dimensions?: Record<string, number>;
};

export type ReliabilityState = {
  ok: boolean;
  reliability?: ReliabilityTruth & Record<string, unknown>;
  governance?: Record<string, unknown>;
  scores?: ReliabilityScores;
  correlation?: { correlations?: { pattern?: string; summary?: string; domains?: string[] }[]; correlation_strength?: number };
  fatigue?: { fatigue_score?: number; surfaced_count?: number; summary?: string };
  recovery?: { degraded_mode?: boolean; recovery_options?: { action?: string; label?: string }[] };
  explainability?: Record<string, unknown>;
  reconstruction?: { operational_story?: string; causal_chains?: { steps?: string[]; confidence?: number }[] };
};

export const fetchReliabilityState = () => mcFetch<ReliabilityState>("/api/v1/reliability/state");

export const fetchReliabilityScores = () =>
  mcFetch<{ ok: boolean; scores?: ReliabilityScores; reliability?: ReliabilityTruth }>("/api/v1/reliability/scores");

export const fetchReliabilityReplay = (windowHours = 48) =>
  mcFetch<{ ok: boolean; operational_story?: string; causal_chains?: unknown[]; replay_graph?: unknown }>(
    `/api/v1/reliability/replay?window_hours=${windowHours}`
  );

export const fetchReliabilityConfidence = () =>
  mcFetch<{ ok: boolean; confidence?: Record<string, unknown>; truth_state?: string; explainability?: string }>(
    "/api/v1/reliability/confidence"
  );

export const fetchReliabilityGovernance = () =>
  mcFetch<{ ok: boolean; governance?: Record<string, unknown>; explainability?: string }>("/api/v1/reliability/governance");

export const fetchReliabilityCorrelation = () =>
  mcFetch<{ ok: boolean; correlation?: ReliabilityState["correlation"] }>("/api/v1/reliability/correlation");

export const reconstructReliabilityReplay = (windowHours = 48) =>
  mcFetch<ReliabilityState["reconstruction"]>("/api/v1/reliability/replay/reconstruct", {
    method: "POST",
    body: JSON.stringify({ window_hours: windowHours }),
  });

export const retryReliabilityRecovery = (action: string) =>
  mcFetch<{ ok: boolean; action?: string; readonly?: boolean }>("/api/v1/reliability/recovery/retry", {
    method: "POST",
    body: JSON.stringify({ action }),
  });
