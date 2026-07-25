/** FIX 300 — multi-tenant platform foundation (tenancy ≠ governance bypass). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type MultiTenantPlatformFoundationResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  tenant_compose_artifacts_only: boolean;
  tenant_authority: boolean;
  automatic_tenant_creation_enabled: boolean;
  cross_tenant_access_enabled: boolean;
  cross_tenant_trust_enabled: boolean;
  permission_escalation_enabled: boolean;
  trust_mutation_authority: boolean;
  repository_mutation_authority: boolean;
  provider_mutation_authority: boolean;
  deployment_authority: boolean;
  rollback_authority: boolean;
  merge_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  multi_tenant_platform_foundation?: Record<string, unknown>;
  markdown?: string;
};

export type MultiTenantPlatformFoundationRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  multi_tenant_platform_foundation_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlMultiTenantPlatformFoundation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<MultiTenantPlatformFoundationResponse>(
    `/api/v1/mission-control/multi-tenant-platform-foundation?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlMultiTenantPlatformFoundationRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    tenantDomain?: string;
    organizationId?: string;
    workspaceId?: string;
    projectId?: string;
  },
) =>
  mcFetch<MultiTenantPlatformFoundationRecordResponse>(
    `/api/v1/mission-control/multi-tenant-platform-foundation/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        tenant_domain: options?.tenantDomain,
        organization_id: options?.organizationId,
        workspace_id: options?.workspaceId,
        project_id: options?.projectId,
      }),
    },
  );
