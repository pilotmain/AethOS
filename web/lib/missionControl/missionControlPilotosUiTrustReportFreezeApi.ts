/** FIX 192 — PilotOS UI trust report freeze (trust_freeze ≠ trust_granting). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PilotosUiTrustReportFreezeResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_reexecution_performed: boolean;
  trust_granting_authority: boolean;
  pilot_execution_authority: boolean;
  cross_repo_authority: boolean;
  automatic_expansion_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  trust_report_composes_artifacts_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  pilotos_ui_trust_report_freeze?: Record<string, unknown>;
  markdown?: string;
};

export type PilotosUiTrustReportFreezeRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  pilotos_ui_trust_report_freeze_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlPilotosUiTrustReportFreeze = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PilotosUiTrustReportFreezeResponse>(
    `/api/v1/mission-control/pilotos-ui-trust-report-freeze?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPilotosUiTrustReportFreezeRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata?: Record<string, unknown>,
) =>
  mcFetch<PilotosUiTrustReportFreezeRecordResponse>(
    `/api/v1/mission-control/pilotos-ui-trust-report-freeze/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        author,
        metadata: metadata ?? {},
      }),
    },
  );
