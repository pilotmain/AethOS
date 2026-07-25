/** FIX 174 — governed lane entry recommendation (composes FIX 169 + FIX 173). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedLaneEntryRecommendationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  lane_admission_performed: boolean;
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
  governed_lane_entry_recommendation?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedLaneEntryRecommendationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_lane_entry_recommendation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedLaneEntryRecommendation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedLaneEntryRecommendationResponse>(
    `/api/v1/mission-control/governed-lane-entry-recommendation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedLaneEntryRecommendationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernedLaneEntryRecommendationRecordResponse>(
    `/api/v1/mission-control/governed-lane-entry-recommendation/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
