/** FIX 260 — multi-repository engineering intelligence (portfolio ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MultiRepositoryEngineeringIntelligenceResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  intelligence_compose_artifacts_only: boolean;
  portfolio_authority: boolean;
  cross_repo_authority: boolean;
  program_delivery_authority: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  provider_mutation_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  multi_repository_engineering_intelligence?: Record<string, unknown>;
  markdown?: string;
};

export type MultiRepositoryEngineeringIntelligenceRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  multi_repository_engineering_intelligence_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlMultiRepositoryEngineeringIntelligence = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MultiRepositoryEngineeringIntelligenceResponse>(
    `/api/v1/mission-control/multi-repository-engineering-intelligence?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlMultiRepositoryEngineeringIntelligenceRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    repository?: string;
    source_repository?: string;
    target_repository?: string;
    relationship?: string;
  },
) =>
  mcFetch<MultiRepositoryEngineeringIntelligenceRecordResponse>(
    `/api/v1/mission-control/multi-repository-engineering-intelligence/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        ...options,
      }),
    },
  );
