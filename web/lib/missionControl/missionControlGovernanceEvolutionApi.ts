/** FIX 155 — governance evolution + institutional continuity (institutional temporal cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceEvolutionResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_governance_evolution_enabled: boolean;
  self_directed_institutional_transformation_enabled: boolean;
  automatic_doctrine_migration_enabled: boolean;
  policy_mutation_authority_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  evolution?: Record<string, unknown>;
  markdown?: string;
};

export type GovernanceEvolutionRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  evolution_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernanceEvolution = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceEvolutionResponse>(
    `/api/v1/mission-control/governance-evolution?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernanceEvolutionRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernanceEvolutionRecordResponse>(`/api/v1/mission-control/governance-evolution/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
