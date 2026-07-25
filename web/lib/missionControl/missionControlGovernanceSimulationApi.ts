/** FIX 144 — governance simulation sandbox (hypothetical only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GovernanceSimulationResponse = {
  ok: boolean;
  read_only: boolean;
  simulation_only: boolean;
  mutation_performed: boolean;
  live_policy_mutation_enabled: boolean;
  auto_policy_update_enabled: boolean;
  automatic_governance_tuning_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  simulation?: Record<string, unknown>;
  markdown?: string;
};

export const fetchMissionControlGovernanceSimulation = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
  scenarios = "all",
) =>
  mcFetch<GovernanceSimulationResponse>(
    `/api/v1/mission-control/governance-simulation?session_id=${encodeURIComponent(sessionId)}&scenarios=${encodeURIComponent(scenarios)}&format=${format}`,
  );
