/** FIX 167 — governed execution handoff coordination (handoff cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ExecutionHandoffCoordinationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  autonomous_lane_entry_enabled: boolean;
  pr_open_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  execution_handoff_coordination?: Record<string, unknown>;
  markdown?: string;
};

export type ExecutionHandoffCoordinationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  execution_handoff_coordination_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlExecutionHandoffCoordination = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ExecutionHandoffCoordinationResponse>(
    `/api/v1/mission-control/execution-handoff-coordination?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlExecutionHandoffCoordinationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<ExecutionHandoffCoordinationRecordResponse>(
    `/api/v1/mission-control/execution-handoff-coordination/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
