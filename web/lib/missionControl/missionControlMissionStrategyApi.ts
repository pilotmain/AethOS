/** FIX 145 — mission strategy layer (read-only strategic reasoning). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionStrategyResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_planning_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_reprioritization_enabled: boolean;
  organizational_self_direction_enabled: boolean;
  automatic_policy_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  strategy?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlMissionStrategy = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MissionStrategyResponse>(
    `/api/v1/mission-control/mission-strategy?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );
