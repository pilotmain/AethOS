/** FIX 187 — independent repository trust expansion (trust is non-transferable). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type IndependentRepositoryTrustExpansionResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  pilot_execution_performed: boolean;
  autonomous_trust_expansion_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  trust_transfer_enabled: boolean;
  automatic_repo_trust_inheritance_enabled: boolean;
  cross_repo_authority_enabled: boolean;
  trust_expansion_composes_artifacts_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  independent_repository_trust_expansion?: Record<string, unknown>;
  markdown?: string;
};

export type IndependentRepositoryTrustExpansionRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  independent_repository_trust_expansion_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlIndependentRepositoryTrustExpansion = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<IndependentRepositoryTrustExpansionResponse>(
    `/api/v1/mission-control/independent-repository-trust-expansion?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlIndependentRepositoryTrustExpansionRecord = (
  sessionId: string,
  kind: string,
  content: string,
  repository = "",
  author = "operator",
) =>
  mcFetch<IndependentRepositoryTrustExpansionRecordResponse>(
    `/api/v1/mission-control/independent-repository-trust-expansion/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, repository, author }),
    },
  );
