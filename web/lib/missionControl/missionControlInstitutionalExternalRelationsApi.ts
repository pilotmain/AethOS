/** FIX 157 — institutional external relations + constitutional boundary (external-relations cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type InstitutionalExternalRelationsResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_external_negotiation_enabled: boolean;
  autonomous_provider_alignment_enabled: boolean;
  self_directed_institutional_diplomacy_enabled: boolean;
  sovereignty_delegation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  external_relations?: Record<string, unknown>;
  markdown?: string;
};

export type InstitutionalExternalRelationsRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  external_relations_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlInstitutionalExternalRelations = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<InstitutionalExternalRelationsResponse>(
    `/api/v1/mission-control/institutional-external-relations?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlInstitutionalExternalRelationsRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<InstitutionalExternalRelationsRecordResponse>(
    `/api/v1/mission-control/institutional-external-relations/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
