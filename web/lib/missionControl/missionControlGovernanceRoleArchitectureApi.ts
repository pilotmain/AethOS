/** FIX 150 — governance role architecture + trust boundaries (read-only topology). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceRoleArchitectureResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  delegated_execution_authority_enabled: boolean;
  automatic_approval_enabled: boolean;
  autonomous_role_elevation_enabled: boolean;
  automatic_policy_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  architecture?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlGovernanceRoleArchitecture = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GovernanceRoleArchitectureResponse>(
    `/api/v1/mission-control/governance-role-architecture?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );
