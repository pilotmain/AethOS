/** FIX 182 — repo pilot readiness dashboard (readiness ≠ execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type RepoPilotReadinessDashboardResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  pilot_execution_performed: boolean;
  autonomous_readiness_mutation_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  readiness_visibility_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  repo_pilot_readiness_dashboard?: Record<string, unknown>;
  markdown?: string;
};

export type RepoPilotReadinessDashboardRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  repo_pilot_readiness_dashboard_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlRepoPilotReadinessDashboard = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<RepoPilotReadinessDashboardResponse>(
    `/api/v1/mission-control/repo-pilot-readiness-dashboard?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlRepoPilotReadinessDashboardRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<RepoPilotReadinessDashboardRecordResponse>(
    `/api/v1/mission-control/repo-pilot-readiness-dashboard/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
