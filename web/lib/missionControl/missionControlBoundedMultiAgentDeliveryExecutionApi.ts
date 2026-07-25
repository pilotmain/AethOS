/** FIX 189 — bounded multi-agent delivery execution (agents work, gates decide). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type BoundedMultiAgentDeliveryExecutionResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  bounded_work_performed: boolean;
  agent_execution_authority: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  railway_authority: boolean;
  provider_authority: boolean;
  gate_bypass_enabled: boolean;
  autonomous_approval_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  bounded_multi_agent_delivery_execution?: Record<string, unknown>;
  markdown?: string;
};

export type BoundedMultiAgentDeliveryExecutionRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  bounded_multi_agent_delivery_execution_memory_only: boolean;
  detail?: string;
};

export type BoundedMultiAgentDeliveryExecutionRunResponse = {
  ok: boolean;
  session_id: string;
  role_id?: string;
  pipeline?: boolean;
  agent_outputs?: Record<string, unknown>[];
  pipeline_state?: string;
  blockers?: string[];
  bounded_work_performed: boolean;
  agent_execution_authority: boolean;
  merge_authority: boolean;
  railway_authority: boolean;
  provider_authority: boolean;
  detail?: string;
};

export const fetchMissionControlBoundedMultiAgentDeliveryExecution = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<BoundedMultiAgentDeliveryExecutionResponse>(
    `/api/v1/mission-control/bounded-multi-agent-delivery-execution?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlBoundedMultiAgentDeliveryExecutionRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<BoundedMultiAgentDeliveryExecutionRecordResponse>(
    `/api/v1/mission-control/bounded-multi-agent-delivery-execution/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );

export const runMissionControlBoundedMultiAgentDeliveryExecution = (
  sessionId = "default",
  roleId = "",
) =>
  mcFetch<BoundedMultiAgentDeliveryExecutionRunResponse>(
    `/api/v1/mission-control/bounded-multi-agent-delivery-execution/run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, role_id: roleId }),
    },
  );
