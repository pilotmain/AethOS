/** FIX 160 — constitutional audit + public accountability (constitutional accountability cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ConstitutionalAuditResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_disclosure_enabled: boolean;
  public_communication_authority_enabled: boolean;
  governance_enforcement_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  constitutional_audit?: Record<string, unknown>;
  markdown?: string;
};

export type ConstitutionalAuditRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  constitutional_audit_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlConstitutionalAudit = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<ConstitutionalAuditResponse>(
    `/api/v1/mission-control/constitutional-audit?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlConstitutionalAuditRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<ConstitutionalAuditRecordResponse>(
    `/api/v1/mission-control/constitutional-audit/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
