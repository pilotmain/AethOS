/** FIX 176 — human lane admission decision (decision ≠ lane entry execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type HumanLaneAdmissionDecisionResponse = {
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
  human_lane_admission_decision?: Record<string, unknown>;
  markdown?: string;
};

export type HumanLaneAdmissionDecisionRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  human_lane_admission_decision_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlHumanLaneAdmissionDecision = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<HumanLaneAdmissionDecisionResponse>(
    `/api/v1/mission-control/human-lane-admission-decision?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlHumanLaneAdmissionDecisionRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<HumanLaneAdmissionDecisionRecordResponse>(
    `/api/v1/mission-control/human-lane-admission-decision/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
