/** FIX 137 — read-only mission/job replay from evidence bundle data. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type JobReplayStep = {
  step_index: number;
  step_id: string;
  link_key?: string;
  link_refs?: Record<string, string>;
  source?: string;
  lane?: string;
  timestamp?: string;
  action?: string;
  detail?: string;
  job_id?: string;
  mutation_performed?: boolean;
  state_before?: Record<string, unknown>;
  state_after?: Record<string, unknown>;
  receipts?: Array<Record<string, unknown>>;
  gates?: Array<Record<string, unknown>>;
  blockers?: Array<Record<string, unknown>>;
  approvals?: Array<Record<string, unknown>>;
};

export type JobReplayPayload = {
  schema_version: string;
  session_id: string;
  job_id?: string | null;
  mission?: Record<string, unknown>;
  step_count: number;
  steps: JobReplayStep[];
  link_index?: Record<string, number>;
  final_state?: Record<string, unknown>;
  read_only: boolean;
  mutation_performed: boolean;
};

export type JobReplayResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  job_id?: string | null;
  detail?: string;
  replay?: JobReplayPayload;
  summary_markdown?: string;
};

export const fetchMissionControlJobReplay = (
  sessionId = "default",
  format: "json" | "summary" | "both" = "both",
  jobId?: string,
) => {
  const params = new URLSearchParams({ session_id: sessionId, format });
  if (jobId) params.set("job_id", jobId);
  return mcFetch<JobReplayResponse>(`/api/v1/mission-control/job-replay?${params.toString()}`);
};

export function jobReplaySummaryFilename(sessionId: string, correlationId?: string): string {
  const slug = (correlationId || sessionId).replace(/[^a-zA-Z0-9_-]+/g, "-").slice(0, 48);
  return `aethos-replay-${slug || "session"}.md`;
}
