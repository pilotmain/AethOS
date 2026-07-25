/** FIX 161 — constitutional legitimacy + institutional trust (constitutional legitimacy cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ConstitutionalLegitimacyResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_legitimacy_enforcement_enabled: boolean;
  public_trust_manipulation_enabled: boolean;
  constitutional_authority_expansion_enabled: boolean;
  sovereignty_delegation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  constitutional_legitimacy?: Record<string, unknown>;
  markdown?: string;
};

export type ConstitutionalLegitimacyRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  constitutional_legitimacy_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlConstitutionalLegitimacy = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ConstitutionalLegitimacyResponse>(
    `/api/v1/mission-control/constitutional-legitimacy?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlConstitutionalLegitimacyRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<ConstitutionalLegitimacyRecordResponse>(
    `/api/v1/mission-control/constitutional-legitimacy/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
