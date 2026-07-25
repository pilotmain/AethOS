/** FIX 148 — governance deliberation workspace (institutional memory only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceDeliberationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_approval_enabled: boolean;
  automatic_rejection_enabled: boolean;
  autonomous_policy_evolution_enabled: boolean;
  delegated_authority_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  workspace?: Record<string, unknown>;
  markdown?: string;
};

export type GovernanceDeliberationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  deliberation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernanceDeliberation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceDeliberationResponse>(
    `/api/v1/mission-control/governance-deliberation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernanceDeliberationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GovernanceDeliberationRecordResponse>(`/api/v1/mission-control/governance-deliberation/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
