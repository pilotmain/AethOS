/** FIX 158 — institutional existential risk + continuity preservation (existential continuity cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type InstitutionalExistentialRiskResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_self_preservation_enabled: boolean;
  autonomous_continuity_enforcement_enabled: boolean;
  constitutional_override_authority_enabled: boolean;
  institutional_self_defense_authority_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  existential_risk?: Record<string, unknown>;
  markdown?: string;
};

export type InstitutionalExistentialRiskRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  existential_risk_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlInstitutionalExistentialRisk = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<InstitutionalExistentialRiskResponse>(
    `/api/v1/mission-control/institutional-existential-risk?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlInstitutionalExistentialRiskRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<InstitutionalExistentialRiskRecordResponse>(
    `/api/v1/mission-control/institutional-existential-risk/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
