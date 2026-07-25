/** FIX 172 — governed task execution coordination (coordinate without executing). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedTaskExecutionCoordinationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_lane_entry_enabled: boolean;
  autonomous_approval_enabled: boolean;
  tier_escalation_enabled: boolean;
  gate_bypass_enabled: boolean;
  code_write_enabled: boolean;
  pr_action_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  governed_task_execution_coordination?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedTaskExecutionCoordinationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_task_execution_coordination_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedTaskExecutionCoordination = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedTaskExecutionCoordinationResponse>(
    `/api/v1/mission-control/governed-task-execution-coordination?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedTaskExecutionCoordinationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernedTaskExecutionCoordinationRecordResponse>(
    `/api/v1/mission-control/governed-task-execution-coordination/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
