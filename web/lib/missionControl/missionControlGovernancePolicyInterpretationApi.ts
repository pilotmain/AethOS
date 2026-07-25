/** FIX 152 — governance policy interpretation + precedent application (institutional constitutional reasoning). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernancePolicyInterpretationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  automatic_doctrine_enforcement_enabled: boolean;
  autonomous_governance_rulings_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  interpretation?: Record<string, unknown>;
  markdown?: string;
};

export type GovernancePolicyInterpretationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  interpretation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernancePolicyInterpretation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernancePolicyInterpretationResponse>(
    `/api/v1/mission-control/governance-policy-interpretation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernancePolicyInterpretationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernancePolicyInterpretationRecordResponse>(
    `/api/v1/mission-control/governance-policy-interpretation/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
