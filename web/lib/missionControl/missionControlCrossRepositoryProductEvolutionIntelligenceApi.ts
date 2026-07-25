/** FIX 261 — cross-repository product evolution intelligence (evolution ≠ execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CrossRepositoryProductEvolutionIntelligenceResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  intelligence_compose_artifacts_only: boolean;
  product_evolution_authority: boolean;
  automatic_improvement_enabled: boolean;
  cross_repo_execution_enabled: boolean;
  repository_mutation_authority: boolean;
  trust_mutation_authority: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  provider_mutation_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  cross_repository_product_evolution_intelligence?: Record<string, unknown>;
  markdown?: string;
};

export type CrossRepositoryProductEvolutionIntelligenceRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  cross_repository_product_evolution_intelligence_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlCrossRepositoryProductEvolutionIntelligence = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<CrossRepositoryProductEvolutionIntelligenceResponse>(
    `/api/v1/mission-control/cross-repository-product-evolution-intelligence?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlCrossRepositoryProductEvolutionIntelligenceRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    repository?: string;
    domain?: string;
    targetRepository?: string;
    opportunityId?: string;
  },
) =>
  mcFetch<CrossRepositoryProductEvolutionIntelligenceRecordResponse>(
    `/api/v1/mission-control/cross-repository-product-evolution-intelligence/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        repository: options?.repository,
        domain: options?.domain,
        target_repository: options?.targetRepository,
        opportunity_id: options?.opportunityId,
      }),
    },
  );
