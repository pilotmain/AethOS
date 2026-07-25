/** FIX 171 — bounded execution participation (envelope-scoped agent coordination). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type BoundedExecutionParticipationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_lane_entry_enabled: boolean;
  autonomous_approval_enabled: boolean;
  tier_escalation_enabled: boolean;
  gate_bypass_enabled: boolean;
  pr_open_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  bounded_execution_participation?: Record<string, unknown>;
  markdown?: string;
};

export type BoundedExecutionParticipationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  bounded_execution_participation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlBoundedExecutionParticipation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<BoundedExecutionParticipationResponse>(
    `/api/v1/mission-control/bounded-execution-participation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlBoundedExecutionParticipationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<BoundedExecutionParticipationRecordResponse>(
    `/api/v1/mission-control/bounded-execution-participation/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
