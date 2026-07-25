/** FIX 305 — billing & entitlements foundation (entitlements ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type BillingEntitlementsFoundationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  billing_entitlements_compose_artifacts_only: boolean;
  billing_authority: boolean;
  automatic_subscription_creation_enabled: boolean;
  automatic_plan_upgrade_enabled: boolean;
  automatic_plan_downgrade_enabled: boolean;
  payment_processing_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  billing_entitlements_foundation?: Record<string, unknown>;
  markdown?: string;
};

export type BillingEntitlementsFoundationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  billing_entitlements_foundation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlBillingEntitlementsFoundation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<BillingEntitlementsFoundationResponse>(
    `/api/v1/mission-control/billing-entitlements-foundation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlBillingEntitlementsFoundationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  plan?: string,
) =>
  mcFetch<BillingEntitlementsFoundationRecordResponse>(
    `/api/v1/mission-control/billing-entitlements-foundation/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        plan,
      }),
    },
  );
