/** FIX 179 — frozen gate execution request adapter (execution request ≠ execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type FrozenGateExecutionRequestAdapterResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  command_execution_performed: boolean;
  gate_execution_performed: boolean;
  lane_entry_execution_performed: boolean;
  lane_admission_executed: boolean;
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
  frozen_gate_execution_request_adapter?: Record<string, unknown>;
  markdown?: string;
};

export type FrozenGateExecutionRequestAdapterRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  frozen_gate_execution_request_adapter_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlFrozenGateExecutionRequestAdapter = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<FrozenGateExecutionRequestAdapterResponse>(
    `/api/v1/mission-control/frozen-gate-execution-request-adapter?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlFrozenGateExecutionRequestAdapterRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<FrozenGateExecutionRequestAdapterRecordResponse>(
    `/api/v1/mission-control/frozen-gate-execution-request-adapter/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
