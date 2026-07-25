/** FIX 310 — Customer support & success foundation (visibility ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CustomerSupportSuccessFoundationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  customer_support_compose_artifacts_only: boolean;
  customer_support_authority: boolean;
  automatic_customer_contact_enabled: boolean;
  automatic_escalation_enabled: boolean;
  automatic_support_resolution_enabled: boolean;
  automatic_plan_upgrade_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  customer_support_success_foundation?: Record<string, unknown>;
  markdown?: string;
};

export type CustomerSupportSuccessFoundationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  customer_support_success_foundation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlCustomerSupportSuccessFoundation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<CustomerSupportSuccessFoundationResponse>(
    `/api/v1/mission-control/customer-support-success-foundation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlCustomerSupportSuccessFoundationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
  orgId?: string,
) =>
  mcFetch<CustomerSupportSuccessFoundationRecordResponse>(
    `/api/v1/mission-control/customer-support-success-foundation`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        domain,
        org_id: orgId,
      }),
    },
  );
