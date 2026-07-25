/** FIX 165 — mission planning multi-agent deliberation (bounded agent analysis). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionPlanningDeliberationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  autonomous_lane_selection_enabled: boolean;
  autonomous_pr_creation_enabled: boolean;
  autonomous_railway_mutation_enabled: boolean;
  autonomous_merge_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  mission_planning_deliberation?: Record<string, unknown>;
  markdown?: string;
};

export type MissionPlanningDeliberationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  mission_planning_deliberation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlMissionPlanningDeliberation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MissionPlanningDeliberationResponse>(
    `/api/v1/mission-control/mission-planning-deliberation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlMissionPlanningDeliberationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<MissionPlanningDeliberationRecordResponse>(
    `/api/v1/mission-control/mission-planning-deliberation/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
