/** FIX 142 — operator contextual guidance (recommendation-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type OperatorGuidanceRecommendation = {
  kind: string;
  guidance: string;
  rationale?: string;
  suggested_phrase?: string;
  priority?: string;
  executable: boolean;
  operator_approval_required: boolean;
};

export type OperatorGuidancePayload = {
  schema_version: string;
  session_id: string;
  recommendation_count: number;
  all_recommendations_executable: boolean;
  operator_approval_required_for_all: boolean;
  sections: Record<string, OperatorGuidanceRecommendation[]>;
};

export type OperatorGuidanceResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  autonomous_execution_enabled: boolean;
  automatic_mutation_planning_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  guidance?: OperatorGuidancePayload;
  markdown?: string;
};

export const fetchMissionControlOperatorGuidance = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
  focus?: string,
) => {
  const params = new URLSearchParams({ session_id: sessionId, format });
  if (focus) params.set("focus", focus);
  return mcFetch<OperatorGuidanceResponse>(`/api/v1/mission-control/operator-guidance?${params.toString()}`);
};
