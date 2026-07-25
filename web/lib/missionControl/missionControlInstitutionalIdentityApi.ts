/** FIX 156 — institutional identity + constitutional intent (institutional identity cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type InstitutionalIdentityResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_institutional_redirection_enabled: boolean;
  self_authored_mission_changes_enabled: boolean;
  automatic_constitutional_rewriting_enabled: boolean;
  governance_sovereignty_delegated: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  identity?: Record<string, unknown>;
  markdown?: string;
};

export type InstitutionalIdentityRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  identity_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlInstitutionalIdentity = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<InstitutionalIdentityResponse>(
    `/api/v1/mission-control/institutional-identity?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlInstitutionalIdentityRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<InstitutionalIdentityRecordResponse>(`/api/v1/mission-control/institutional-identity/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
