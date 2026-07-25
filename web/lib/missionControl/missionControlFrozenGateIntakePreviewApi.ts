/** FIX 178 — frozen gate intake preview (intake preview ≠ gate execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type FrozenGateIntakePreviewResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
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
  frozen_gate_intake_preview?: Record<string, unknown>;
  markdown?: string;
};

export type FrozenGateIntakePreviewRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  frozen_gate_intake_preview_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlFrozenGateIntakePreview = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<FrozenGateIntakePreviewResponse>(
    `/api/v1/mission-control/frozen-gate-intake-preview?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlFrozenGateIntakePreviewRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<FrozenGateIntakePreviewRecordResponse>(
    `/api/v1/mission-control/frozen-gate-intake-preview/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
