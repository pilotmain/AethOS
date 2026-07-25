/** FIX 186 — dogfood pilot trust report freeze (trust_report_freeze ≠ pilot_execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type DogfoodPilotTrustReportFreezeResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  pilot_reexecution_performed: boolean;
  autonomous_trust_report_execution_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  trust_report_composes_artifacts_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  dogfood_pilot_trust_report_freeze?: Record<string, unknown>;
  markdown?: string;
};

export type DogfoodPilotTrustReportFreezeRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  dogfood_pilot_trust_report_freeze_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlDogfoodPilotTrustReportFreeze = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<DogfoodPilotTrustReportFreezeResponse>(
    `/api/v1/mission-control/dogfood-pilot-trust-report-freeze?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlDogfoodPilotTrustReportFreezeRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<DogfoodPilotTrustReportFreezeRecordResponse>(
    `/api/v1/mission-control/dogfood-pilot-trust-report-freeze/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
