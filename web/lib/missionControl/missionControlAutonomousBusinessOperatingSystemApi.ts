/** FIX 290 — autonomous business operating system (business ≠ authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type AutonomousBusinessOperatingSystemResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  business_compose_artifacts_only: boolean;
  business_authority: boolean;
  automatic_business_execution_enabled: boolean;
  customer_mutation_authority: boolean;
  billing_authority: boolean;
  repository_mutation_authority: boolean;
  deployment_authority: boolean;
  rollback_authority: boolean;
  trust_mutation_authority: boolean;
  merge_authority: boolean;
  provider_mutation_authority: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  autonomous_business_operating_system?: Record<string, unknown>;
  markdown?: string;
};

export type AutonomousBusinessOperatingSystemRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  autonomous_business_operating_system_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlAutonomousBusinessOperatingSystem = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<AutonomousBusinessOperatingSystemResponse>(
    `/api/v1/mission-control/autonomous-business-operating-system?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlAutonomousBusinessOperatingSystemRecord = (
  sessionId: string,
  kind: string,
  content: string,
  options?: {
    businessDomain?: string;
    goalId?: string;
    opportunityId?: string;
  },
) =>
  mcFetch<AutonomousBusinessOperatingSystemRecordResponse>(
    `/api/v1/mission-control/autonomous-business-operating-system/record`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        business_domain: options?.businessDomain,
        goal_id: options?.goalId,
        opportunity_id: options?.opportunityId,
      }),
    },
  );
