/** FIX 143 — meta-governance insights (read-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceInsightsResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  policy_auto_tuning_enabled: boolean;
  governance_self_modification_enabled: boolean;
  autonomous_optimization_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  insights?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlGovernanceInsights = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceInsightsResponse>(
    `/api/v1/mission-control/governance-insights?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );
