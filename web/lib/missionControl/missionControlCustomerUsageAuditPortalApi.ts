/** FIX 307 — customer usage & audit portal (visibility ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CustomerUsageAuditPortalResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  customer_usage_audit_compose_artifacts_only: boolean;
  audit_authority: boolean;
  audit_mutation_enabled: boolean;
  evidence_mutation_enabled: boolean;
  cross_tenant_audit_access_enabled: boolean;
  authorization_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  customer_usage_audit_portal?: Record<string, unknown>;
  markdown?: string;
};

export type CustomerUsageAuditPortalRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  customer_usage_audit_portal_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlCustomerUsageAuditPortal = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<CustomerUsageAuditPortalResponse>(
    `/api/v1/mission-control/customer-usage-audit-portal?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlCustomerUsageAuditPortalRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<CustomerUsageAuditPortalRecordResponse>(
    `/api/v1/mission-control/customer-usage-audit-portal/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        domain,
      }),
    },
  );
