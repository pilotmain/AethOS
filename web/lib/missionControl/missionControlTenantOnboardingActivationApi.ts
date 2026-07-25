/** FIX 301 — tenant onboarding and activation (guidance ≠ platform authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type TenantOnboardingActivationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  onboarding_compose_artifacts_only: boolean;
  onboarding_authority: boolean;
  automatic_provisioning_enabled: boolean;
  automatic_permission_granting_enabled: boolean;
  secret_collection_enabled: boolean;
  provider_mutation_authority: boolean;
  cross_tenant_access_enabled: boolean;
  trust_mutation_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  tenant_onboarding_activation?: Record<string, unknown>;
  markdown?: string;
};

export type TenantOnboardingActivationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  tenant_onboarding_activation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlTenantOnboardingActivation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<TenantOnboardingActivationResponse>(
    `/api/v1/mission-control/tenant-onboarding-activation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlTenantOnboardingActivationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    onboardingStep?: string;
    organizationId?: string;
    workspaceId?: string;
    projectId?: string;
  },
) =>
  mcFetch<TenantOnboardingActivationRecordResponse>(
    `/api/v1/mission-control/tenant-onboarding-activation/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        onboarding_step: options?.onboardingStep,
        organization_id: options?.organizationId,
        workspace_id: options?.workspaceId,
        project_id: options?.projectId,
      }),
    },
  );
