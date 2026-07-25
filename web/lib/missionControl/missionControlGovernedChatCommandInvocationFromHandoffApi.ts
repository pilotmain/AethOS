/** FIX 180 — governed chat command invocation from handoff (invocation ≠ direct execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedChatCommandInvocationFromHandoffResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  gate_execution_performed: boolean;
  hidden_command_execution_performed: boolean;
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
  chat_governance_required: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  governed_chat_command_invocation_from_handoff?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedChatCommandInvocationFromHandoffRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_chat_command_invocation_from_handoff_memory_only: boolean;
  detail?: string;
};

export type GovernedChatCommandInvocationFromHandoffInvokeResponse = {
  ok: boolean;
  session_id: string;
  frozen_chat_command?: string;
  governed_chat_message?: string;
  chat_intent?: string;
  route_id?: string;
  reply?: string;
  audit_id?: string;
  chat_governance_routed: boolean;
  direct_provider_mutation_performed: boolean;
  handoff_invocation_origin?: string;
  handoff_invocation_channel?: string;
  detail?: string;
};

export const fetchMissionControlGovernedChatCommandInvocationFromHandoff = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedChatCommandInvocationFromHandoffResponse>(
    `/api/v1/mission-control/governed-chat-command-invocation-from-handoff?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedChatCommandInvocationFromHandoffRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernedChatCommandInvocationFromHandoffRecordResponse>(
    `/api/v1/mission-control/governed-chat-command-invocation-from-handoff/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );

export const invokeMissionControlGovernedChatCommandFromHandoff = (sessionId = "default") =>
  mcFetch<GovernedChatCommandInvocationFromHandoffInvokeResponse>(
    `/api/v1/mission-control/governed-chat-command-invocation-from-handoff/invoke`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
