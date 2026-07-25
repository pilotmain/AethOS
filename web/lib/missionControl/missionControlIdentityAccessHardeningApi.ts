/** FIX 302 — identity and access hardening (enforcement ≠ escalation). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type IdentityAccessHardeningResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  identity_access_compose_artifacts_only: boolean;
  authorization_authority: boolean;
  automatic_permission_granting_enabled: boolean;
  automatic_role_escalation_enabled: boolean;
  cross_tenant_access_enabled: boolean;
  authorization_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  identity_access_hardening?: Record<string, unknown>;
  markdown?: string;
};

export type IdentityAccessHardeningRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  identity_access_hardening_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlIdentityAccessHardening = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<IdentityAccessHardeningResponse>(
    `/api/v1/mission-control/identity-access-hardening?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlIdentityAccessHardeningRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: { organizationId?: string; userId?: string },
) =>
  mcFetch<IdentityAccessHardeningRecordResponse>(
    `/api/v1/mission-control/identity-access-hardening/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        organization_id: options?.organizationId,
        user_id: options?.userId,
      }),
    },
  );
