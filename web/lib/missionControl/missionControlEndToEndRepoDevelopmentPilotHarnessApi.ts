/** FIX 181 — end-to-end repo development pilot harness (pilot ≠ autonomous execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type EndToEndRepoDevelopmentPilotHarnessResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  autonomous_pipeline_execution_enabled: boolean;
  gate_bypass_enabled: boolean;
  merge_enabled: boolean;
  deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  production_coupling_enabled: boolean;
  governance_mutation_performed: boolean;
  chat_governance_required: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  end_to_end_repo_development_pilot_harness?: Record<string, unknown>;
  markdown?: string;
};

export type EndToEndRepoDevelopmentPilotHarnessRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  end_to_end_repo_development_pilot_harness_memory_only: boolean;
  detail?: string;
};

export type EndToEndRepoDevelopmentPilotHarnessRunResponse = {
  ok: boolean;
  session_id: string;
  repo_issue?: string;
  stages_completed?: string[];
  chat_steps?: Record<string, unknown>[];
  pilot_report?: Record<string, unknown>;
  audit_id?: string;
  blockers?: string[];
  chat_governance_routed: boolean;
  direct_provider_mutation_performed: boolean;
  autonomous_pipeline_execution_enabled: boolean;
  pilot_harness_origin?: string;
  pilot_harness_channel?: string;
  detail?: string;
};

export const fetchMissionControlEndToEndRepoDevelopmentPilotHarness = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<EndToEndRepoDevelopmentPilotHarnessResponse>(
    `/api/v1/mission-control/end-to-end-repo-development-pilot-harness?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlEndToEndRepoDevelopmentPilotHarnessRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<EndToEndRepoDevelopmentPilotHarnessRecordResponse>(
    `/api/v1/mission-control/end-to-end-repo-development-pilot-harness/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );

export const runMissionControlEndToEndRepoDevelopmentPilotHarness = (
  sessionId = "default",
  repoIssue?: string,
) =>
  mcFetch<EndToEndRepoDevelopmentPilotHarnessRunResponse>(
    `/api/v1/mission-control/end-to-end-repo-development-pilot-harness/run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, repo_issue: repoIssue }),
    },
  );
