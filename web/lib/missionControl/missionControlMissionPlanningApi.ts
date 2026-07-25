/** FIX 164 — mission planning + institutional action cognition (planning cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionPlanningResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_action_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  auto_path_selection_enabled: boolean;
  railway_mutation_enabled: boolean;
  pr_open_enabled: boolean;
  merge_deploy_restart_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  mission_planning?: Record<string, unknown>;
  markdown?: string;
};

export type MissionPlanningRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  mission_planning_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlMissionPlanning = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MissionPlanningResponse>(
    `/api/v1/mission-control/mission-planning?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlMissionPlanningRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<MissionPlanningRecordResponse>(`/api/v1/mission-control/mission-planning/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
