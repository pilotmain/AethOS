/** FIX 250 — governed application generation (application_generation ≠ autonomous_authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernedApplicationGenerationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  generation_compose_evidence_only: boolean;
  application_generation_authority: boolean;
  repository_creation_authority: boolean;
  github_mutation_authority: boolean;
  provider_authority: boolean;
  deployment_authority: boolean;
  code_generation_authority: boolean;
  merge_authority: boolean;
  rollback_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  governed_application_generation?: Record<string, unknown>;
  markdown?: string;
};

export type GovernedApplicationGenerationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  governed_application_generation_memory_only: boolean;
  detail?: string;
};

export type GovernedApplicationGenerationHandoffResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  delivery_pipeline_handoff?: Record<string, unknown>;
  application_generation_authority: boolean;
  repository_creation_authority: boolean;
  executable: boolean;
  detail?: string;
};

export const fetchMissionControlGovernedApplicationGeneration = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernedApplicationGenerationResponse>(
    `/api/v1/mission-control/governed-application-generation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernedApplicationGenerationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
  metadata: Record<string, unknown> = {},
) =>
  mcFetch<GovernedApplicationGenerationRecordResponse>(
    `/api/v1/mission-control/governed-application-generation/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author, metadata }),
    },
  );

export const prepareMissionControlGovernedApplicationGenerationHandoff = (sessionId = "default") =>
  mcFetch<GovernedApplicationGenerationHandoffResponse>(
    `/api/v1/mission-control/governed-application-generation/handoff`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
