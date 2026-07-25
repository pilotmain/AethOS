/** FIX 138 — governed rerun plan (read-only, no execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type RerunPlanPayload = {
  schema_version: string;
  session_id: string;
  plan_id?: string;
  correlation_id?: string;
  read_only: boolean;
  mutation_performed: boolean;
  rerun_execution_enabled: boolean;
  eligibility: {
    eligible_for_planning?: boolean;
    eligible_for_execution?: boolean;
    summary?: string;
  };
  replay_derived_plan: Record<string, unknown>;
  blast_radius: Record<string, unknown>;
  dependencies: Array<Record<string, string>>;
  stale_state: Record<string, unknown>;
  rollback_posture: Record<string, unknown>;
  required_approvals: Array<Record<string, unknown>>;
  rerun_blockers: Array<{ code?: string; detail?: string }>;
  mutation_preview: Record<string, unknown>;
  exact_rerun_phrases: Array<{ kind?: string; phrase?: string; executable?: boolean; note?: string }>;
};

export type RerunPlanResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  rerun_execution_enabled: boolean;
  schema_version: string;
  session_id: string;
  job_id?: string | null;
  detail?: string;
  plan?: RerunPlanPayload;
  markdown?: string;
};

export const fetchMissionControlRerunPlan = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
  opts?: { jobId?: string; fromStep?: number; linkKey?: string },
) => {
  const params = new URLSearchParams({ session_id: sessionId, format });
  if (opts?.jobId) params.set("job_id", opts.jobId);
  if (opts?.fromStep != null) params.set("from_step", String(opts.fromStep));
  if (opts?.linkKey) params.set("link_key", opts.linkKey);
  return mcFetch<RerunPlanResponse>(`/api/v1/mission-control/rerun-plan?${params.toString()}`);
};
