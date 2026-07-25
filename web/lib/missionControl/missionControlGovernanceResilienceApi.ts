/** FIX 154 — governance resilience + stress simulation (institutional resilience cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceResilienceResponse = {
  ok: boolean;
  read_only: boolean;
  simulation_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  automatic_governance_adaptation_enabled: boolean;
  autonomous_resilience_correction_enabled: boolean;
  self_healing_governance_enabled: boolean;
  override_authority_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  resilience?: Record<string, unknown>;
  markdown?: string;
};

export type GovernanceResilienceRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  simulation_only: boolean;
  resilience_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernanceResilience = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceResilienceResponse>(
    `/api/v1/mission-control/governance-resilience?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernanceResilienceRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernanceResilienceRecordResponse>(`/api/v1/mission-control/governance-resilience/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
