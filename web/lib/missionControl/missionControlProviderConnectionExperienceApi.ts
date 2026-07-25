/** FIX 303 — provider connection experience (guidance ≠ mutation). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ProviderConnectionExperienceResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  provider_connection_compose_artifacts_only: boolean;
  provider_connection_authority: boolean;
  automatic_provider_connection_enabled: boolean;
  provider_mutation_authority: boolean;
  secret_collection_enabled: boolean;
  permission_escalation_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  provider_connection_experience?: Record<string, unknown>;
  markdown?: string;
};

export type ProviderConnectionExperienceRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  provider_connection_experience_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlProviderConnectionExperience = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ProviderConnectionExperienceResponse>(
    `/api/v1/mission-control/provider-connection-experience?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlProviderConnectionExperienceRecord = (
  sessionId: string,
  kind: string,
  content: string,
  provider?: string,
) =>
  mcFetch<ProviderConnectionExperienceRecordResponse>(
    `/api/v1/mission-control/provider-connection-experience/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        provider,
      }),
    },
  );
