/** FIX 308 — payment integration readiness (readiness ≠ processing). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PaymentIntegrationReadinessResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  payment_readiness_compose_artifacts_only: boolean;
  payment_processing_enabled: boolean;
  credit_card_storage_enabled: boolean;
  automatic_charging_enabled: boolean;
  automatic_refund_enabled: boolean;
  subscription_mutation_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  payment_integration_readiness?: Record<string, unknown>;
  markdown?: string;
};

export type PaymentIntegrationReadinessRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  payment_integration_readiness_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlPaymentIntegrationReadiness = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PaymentIntegrationReadinessResponse>(
    `/api/v1/mission-control/payment-integration-readiness?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPaymentIntegrationReadinessRecord = (
  sessionId: string,
  kind: string,
  content: string,
  provider?: string,
) =>
  mcFetch<PaymentIntegrationReadinessRecordResponse>(
    `/api/v1/mission-control/payment-integration-readiness/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        provider,
      }),
    },
  );
