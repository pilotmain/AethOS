/** FIX 170 — mission authorization (bounded work envelope). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionAuthorizationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  autonomous_lane_expansion_enabled: boolean;
  tier_escalation_enabled: boolean;
  gate_bypass_enabled: boolean;
  pr_open_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  mission_authorization?: Record<string, unknown>;
  markdown?: string;
};

export type MissionAuthorizationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  mission_authorization_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlMissionAuthorization = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MissionAuthorizationResponse>(
    `/api/v1/mission-control/mission-authorization?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlMissionAuthorizationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<MissionAuthorizationRecordResponse>(`/api/v1/mission-control/mission-authorization/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
