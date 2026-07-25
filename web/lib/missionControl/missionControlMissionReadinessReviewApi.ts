/** FIX 147 — mission readiness review board (advisory, human review required). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MissionReadinessReviewResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  human_review_required: boolean;
  autonomous_go_no_go_execution_enabled: boolean;
  autonomous_readiness_decision_enabled: boolean;
  execution_authority_delegated: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  review?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlMissionReadinessReview = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MissionReadinessReviewResponse>(
    `/api/v1/mission-control/mission-readiness-review?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );
