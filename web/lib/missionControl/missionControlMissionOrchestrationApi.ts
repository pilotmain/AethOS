/** FIX 146 — coordinated mission orchestration (read-only coordination cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionOrchestrationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_orchestration_enabled: boolean;
  autonomous_sequencing_execution_enabled: boolean;
  autonomous_approval_batching_enabled: boolean;
  autonomous_promotion_deploy_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  orchestration?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlMissionOrchestration = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MissionOrchestrationResponse>(
    `/api/v1/mission-control/mission-orchestration?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );
