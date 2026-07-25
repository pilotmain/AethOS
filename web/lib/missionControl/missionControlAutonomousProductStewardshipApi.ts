/** FIX 270 — autonomous product stewardship (stewardship ≠ execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AutonomousProductStewardshipResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  stewardship_compose_artifacts_only: boolean;
  product_stewardship_authority: boolean;
  automatic_improvement_enabled: boolean;
  cross_repo_execution_enabled: boolean;
  repository_mutation_authority: boolean;
  deployment_authority: boolean;
  trust_mutation_authority: boolean;
  merge_authority: boolean;
  provider_mutation_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  autonomous_product_stewardship?: Record<string, unknown>;
  markdown?: string;
};

export type AutonomousProductStewardshipRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  autonomous_product_stewardship_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlAutonomousProductStewardship = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<AutonomousProductStewardshipResponse>(
    `/api/v1/mission-control/autonomous-product-stewardship?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlAutonomousProductStewardshipRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    repository?: string;
    domain?: string;
    opportunityId?: string;
  },
) =>
  mcFetch<AutonomousProductStewardshipRecordResponse>(
    `/api/v1/mission-control/autonomous-product-stewardship/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        repository: options?.repository,
        domain: options?.domain,
        opportunity_id: options?.opportunityId,
      }),
    },
  );
