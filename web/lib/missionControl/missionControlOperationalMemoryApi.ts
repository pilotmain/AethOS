/** FIX 139 — operational memory / knowledge graph (read-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type OperationalMemoryGraphPayload = {
  schema_version: string;
  session_id: string;
  plan_id?: string;
  correlation_id?: string;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_adaptation_enabled: boolean;
  graph: {
    nodes: Array<Record<string, unknown>>;
    edges: Array<Record<string, unknown>>;
    stats?: { node_count?: number; edge_count?: number; nodes_by_kind?: Record<string, number> };
  };
  correlated_executions: Array<Record<string, unknown>>;
  repeated_failures: Array<Record<string, unknown>>;
  historical_blast_radius: Record<string, unknown>;
  recurring_blockers: Array<Record<string, unknown>>;
  mission_lineage: Array<Record<string, unknown>>;
  cross_domain_links: Array<Record<string, unknown>>;
  learning_signals: Array<Record<string, unknown>>;
  sources?: Record<string, boolean>;
};

export type OperationalMemoryResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_adaptation_enabled: boolean;
  schema_version: string;
  session_id: string;
  job_id?: string | null;
  detail?: string;
  graph?: OperationalMemoryGraphPayload;
  markdown?: string;
};

export const fetchMissionControlOperationalMemory = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
  opts?: { jobId?: string; includeReplay?: boolean; includeRerunPlan?: boolean },
) => {
  const params = new URLSearchParams({ session_id: sessionId, format });
  if (opts?.jobId) params.set("job_id", opts.jobId);
  if (opts?.includeReplay === false) params.set("include_replay", "false");
  if (opts?.includeRerunPlan === false) params.set("include_rerun_plan", "false");
  return mcFetch<OperationalMemoryResponse>(
    `/api/v1/mission-control/operational-memory?${params.toString()}`,
  );
};
