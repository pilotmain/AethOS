/** FIX 149 — multi-operator governance collaboration (institutional continuity). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceCollaborationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  delegated_execution_authority_enabled: boolean;
  automatic_quorum_approval_enabled: boolean;
  automatic_merge_deploy_enabled: boolean;
  autonomous_organizational_decisions_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  collaboration?: Record<string, unknown>;
  markdown?: string;
};

export type GovernanceCollaborationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  collaboration_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGovernanceCollaboration = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceCollaborationResponse>(
    `/api/v1/mission-control/governance-collaboration?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGovernanceCollaborationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  reviewerName = "",
  reviewerRole = "",
) =>
  mcFetch<GovernanceCollaborationRecordResponse>(`/api/v1/mission-control/governance-collaboration/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      kind,
      content,
      reviewer_name: reviewerName,
      reviewer_role: reviewerRole,
    }),
  });
