/** FIX 177 — gate-routed lane entry handoff (handoff ≠ lane entry execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GateRoutedLaneEntryHandoffResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
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
  gate_routed_lane_entry_handoff?: Record<string, unknown>;
  markdown?: string;
};

export type GateRoutedLaneEntryHandoffRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  gate_routed_lane_entry_handoff_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGateRoutedLaneEntryHandoff = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GateRoutedLaneEntryHandoffResponse>(
    `/api/v1/mission-control/gate-routed-lane-entry-handoff?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGateRoutedLaneEntryHandoffRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GateRoutedLaneEntryHandoffRecordResponse>(
    `/api/v1/mission-control/gate-routed-lane-entry-handoff/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
