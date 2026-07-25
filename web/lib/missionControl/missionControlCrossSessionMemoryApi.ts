/** FIX 140 — cross-session organizational memory (read-only persistence). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CrossSessionOrganizationalMemory = {
  missions_across_sessions: Array<Record<string, unknown>>;
  recurring_incidents: Array<Record<string, unknown>>;
  pr_lineage_across_sessions: Array<Record<string, unknown>>;
  historical_blockers: Array<Record<string, unknown>>;
  operator_history: Array<Record<string, unknown>>;
  mission_ancestry: Array<Record<string, unknown>>;
  approval_risk_patterns: Array<Record<string, unknown>>;
  rollout_lineage: Array<Record<string, unknown>>;
  evidence_stitching: Array<Record<string, unknown>>;
};

export type CrossSessionMemoryPayload = {
  schema_version: string;
  focal_session_id: string;
  persisted_record_count: number;
  ingested_current_session: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_adaptation_enabled: boolean;
  autonomous_optimization_enabled: boolean;
  organizational_memory: CrossSessionOrganizationalMemory;
  learning_signals: Array<Record<string, unknown>>;
};

export type CrossSessionMemoryResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_adaptation_enabled: boolean;
  autonomous_optimization_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  memory?: CrossSessionMemoryPayload;
  markdown?: string;
};

export const fetchMissionControlCrossSessionMemory = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
  opts?: { ingestCurrent?: boolean; limit?: number },
) => {
  const params = new URLSearchParams({ session_id: sessionId, format });
  if (opts?.ingestCurrent === false) params.set("ingest_current", "false");
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  return mcFetch<CrossSessionMemoryResponse>(
    `/api/v1/mission-control/operational-memory/cross-session?${params.toString()}`,
  );
};
