/** FIX 295 — autonomous capability registry & self-awareness (awareness ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AutonomousCapabilityRegistryResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  capability_compose_artifacts_only: boolean;
  capability_authority: boolean;
  self_authority_granting_enabled: boolean;
  automatic_capability_promotion_enabled: boolean;
  trust_mutation_authority: boolean;
  repository_mutation_authority: boolean;
  provider_mutation_authority: boolean;
  deployment_authority: boolean;
  rollback_authority: boolean;
  merge_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  autonomous_capability_registry?: Record<string, unknown>;
  markdown?: string;
};

export type AutonomousCapabilityRegistryRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  autonomous_capability_registry_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlAutonomousCapabilityRegistry = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<AutonomousCapabilityRegistryResponse>(
    `/api/v1/mission-control/autonomous-capability-registry?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlAutonomousCapabilityRegistryRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    capabilityId?: string;
    capabilityDomain?: string;
  },
) =>
  mcFetch<AutonomousCapabilityRegistryRecordResponse>(
    `/api/v1/mission-control/autonomous-capability-registry/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        capability_id: options?.capabilityId,
        capability_domain: options?.capabilityDomain,
      }),
    },
  );
