/** FIX 306 — customer administration console (visibility ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type CustomerAdministrationConsoleResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  customer_administration_compose_artifacts_only: boolean;
  administration_authority: boolean;
  automatic_user_creation_enabled: boolean;
  automatic_permission_granting_enabled: boolean;
  cross_tenant_administration_enabled: boolean;
  trust_mutation_authority: boolean;
  billing_mutation_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  customer_administration_console?: Record<string, unknown>;
  markdown?: string;
};

export type CustomerAdministrationConsoleRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  customer_administration_console_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlCustomerAdministrationConsole = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<CustomerAdministrationConsoleResponse>(
    `/api/v1/mission-control/customer-administration-console?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlCustomerAdministrationConsoleRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<CustomerAdministrationConsoleRecordResponse>(
    `/api/v1/mission-control/customer-administration-console/record`,
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
