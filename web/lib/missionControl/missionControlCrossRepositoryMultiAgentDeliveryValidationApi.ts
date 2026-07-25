/** FIX 191 — cross-repository multi-agent delivery validation (validation ≠ trust granting). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CrossRepositoryMultiAgentDeliveryValidationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  validation_compose_artifacts_only: boolean;
  cross_repo_validation_grants_trust: boolean;
  trust_transfer_enabled: boolean;
  merge_authority: boolean;
  deploy_authority: boolean;
  railway_authority: boolean;
  provider_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  cross_repository_multi_agent_delivery_validation?: Record<string, unknown>;
  markdown?: string;
};

export type CrossRepositoryMultiAgentDeliveryValidationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  cross_repository_multi_agent_delivery_validation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlCrossRepositoryMultiAgentDeliveryValidation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<CrossRepositoryMultiAgentDeliveryValidationResponse>(
    `/api/v1/mission-control/cross-repository-multi-agent-delivery-validation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlCrossRepositoryMultiAgentDeliveryValidationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  repository?: string,
) =>
  mcFetch<CrossRepositoryMultiAgentDeliveryValidationRecordResponse>(
    `/api/v1/mission-control/cross-repository-multi-agent-delivery-validation/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author, repository }),
    },
  );
