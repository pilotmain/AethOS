/** FIX 153 — governance coherence + constitutional integrity (institutional coherence intelligence). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceCoherenceResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  automatic_doctrine_enforcement_enabled: boolean;
  autonomous_governance_correction_enabled: boolean;
  self_healing_governance_enabled: boolean;
  constitutional_override_authority_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  coherence?: Record<string, unknown>;
  markdown?: string;
};

export type GovernanceCoherenceRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  coherence_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernanceCoherence = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceCoherenceResponse>(
    `/api/v1/mission-control/governance-coherence?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernanceCoherenceRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernanceCoherenceRecordResponse>(`/api/v1/mission-control/governance-coherence/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
