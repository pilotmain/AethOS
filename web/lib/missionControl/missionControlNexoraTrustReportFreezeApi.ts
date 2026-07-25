/** FIX 196 — Nexora trust report freeze (trust_freeze ≠ trust granting). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type NexoraTrustReportFreezeResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_reexecution_performed: boolean;
  trust_granting_authority: boolean;
  trust_inheritance_enabled: boolean;
  pilot_execution_authority: boolean;
  cross_repo_authority: boolean;
  automatic_expansion_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  trust_report_composes_artifacts_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  nexora_trust_report_freeze?: Record<string, unknown>;
  markdown?: string;
};

export type NexoraTrustReportFreezeRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  nexora_trust_report_freeze_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlNexoraTrustReportFreeze = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<NexoraTrustReportFreezeResponse>(
    `/api/v1/mission-control/nexora-trust-report-freeze?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlNexoraTrustReportFreezeRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata?: Record<string, unknown>,
) =>
  mcFetch<NexoraTrustReportFreezeRecordResponse>(
    `/api/v1/mission-control/nexora-trust-report-freeze/record`,
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
