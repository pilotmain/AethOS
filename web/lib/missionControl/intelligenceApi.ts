/** Operational intelligence — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type OperationalAnomaly = {
  anomaly_id?: string;
  kind?: string;
  severity?: string;
  confidence?: number;
  evidence?: string[];
  related_systems?: string[];
  recommended_action?: string;
};

export type OperationalRecommendation = {
  recommendation_id?: string;
  severity?: string;
  confidence?: number;
  title?: string;
  observed?: string[];
  suggested_action?: string;
  approval_required?: boolean;
  status?: string;
  preflight_id?: string;
  autonomous_execution_blocked?: boolean;
};

export type OperationalIntelligenceState = {
  ok: boolean;
  anomalies?: OperationalAnomaly[];
  recommendations?: OperationalRecommendation[];
  drift?: { detected?: boolean; severity?: string; signals?: string[]; confidence?: number };
  stability?: { stability?: string; event_count?: number; timeline?: { at?: number; detail?: string }[] };
  telemetry_freshness?: { stale?: boolean; stale_sources?: string[]; age_hours?: number };
  recurring_patterns?: string[];
  trends?: string[];
  replays?: { replay_id?: string; created_at?: number; anomaly_count?: number }[];
  scheduler?: { running?: boolean; stats?: { cycles?: number } };
  readonly?: boolean;
  autonomous_execution_blocked?: boolean;
};

export const fetchOperationalIntelligenceState = () =>
  mcFetch<OperationalIntelligenceState>("/api/v1/intelligence/state");

export const runOperationalCycle = () =>
  mcFetch<{ ok: boolean; cycle?: Record<string, unknown> }>("/api/v1/intelligence/cycle", { method: "POST" });

export const dismissRecommendation = (id: string) =>
  mcFetch<{ ok: boolean }>(`/api/v1/intelligence/recommendations/${id}/dismiss`, { method: "POST" });

export const snoozeRecommendation = (id: string, hours = 4) =>
  mcFetch<{ ok: boolean }>(`/api/v1/intelligence/recommendations/${id}/snooze`, {
    method: "POST",
    body: JSON.stringify({ hours }),
  });

export const generatePreflightFromRecommendation = (id: string) =>
  mcFetch<{ ok: boolean; preflight?: { preflight_id?: string } }>(
    `/api/v1/intelligence/recommendations/${id}/generate-preflight`,
    { method: "POST", body: JSON.stringify({ workspace_hint: "aethos" }) },
  );

export const fetchOperationalReplay = (replayId: string) =>
  mcFetch<{ ok: boolean; replay?: Record<string, unknown> }>(`/api/v1/intelligence/replay/${replayId}`);
