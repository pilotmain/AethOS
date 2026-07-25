/** FIX 151 — governance doctrine + policy charter (institutional constitutionality). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceDoctrineResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_doctrine_evolution_enabled: boolean;
  self_modifying_governance_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  doctrine?: Record<string, unknown>;
  markdown?: string;
};

export type GovernanceDoctrineRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  doctrine_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernanceDoctrine = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceDoctrineResponse>(
    `/api/v1/mission-control/governance-doctrine?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernanceDoctrineRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernanceDoctrineRecordResponse>(`/api/v1/mission-control/governance-doctrine/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
