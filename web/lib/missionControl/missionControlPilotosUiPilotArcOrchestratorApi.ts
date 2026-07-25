/** FIX 188 — PilotOS UI pilot arc orchestrator (orchestration ≠ trust granting). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PilotosUiPilotArcOrchestratorResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_execution_performed: boolean;
  automatic_trust_granting_enabled: boolean;
  trust_transfer_enabled: boolean;
  gate_bypass_enabled: boolean;
  merge_enabled: boolean;
  deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  pilotos_ui_pilot_arc_orchestrator?: Record<string, unknown>;
  markdown?: string;
};

export type PilotosUiPilotArcOrchestratorRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  pilotos_ui_pilot_arc_orchestrator_memory_only: boolean;
  detail?: string;
};

export type PilotosUiPilotArcOrchestratorRunResponse = {
  ok: boolean;
  pilot_number: number;
  session_id: string;
  audit_id?: string;
  stages_completed?: string[];
  blockers?: string[];
  automatic_trust_granting_enabled: boolean;
  trust_transfer_enabled: boolean;
  pilot_arc_routes_through_fix_181: boolean;
  detail?: string;
};

export const fetchMissionControlPilotosUiPilotArcOrchestrator = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PilotosUiPilotArcOrchestratorResponse>(
    `/api/v1/mission-control/pilotos-ui-pilot-arc-orchestrator?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPilotosUiPilotArcOrchestratorRecord = (
  sessionId: string,
  kind: string,
  content: string,
  repoIssue = "",
  author = "operator",
) =>
  mcFetch<PilotosUiPilotArcOrchestratorRecordResponse>(
    `/api/v1/mission-control/pilotos-ui-pilot-arc-orchestrator/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, repo_issue: repoIssue, author }),
    },
  );

export const runMissionControlPilotosUiPilotArcOrchestrator = (pilotNumber: 1 | 2 | 3, sessionId = "default") =>
  mcFetch<PilotosUiPilotArcOrchestratorRunResponse>(
    `/api/v1/mission-control/pilotos-ui-pilot-arc-orchestrator/run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pilot_number: pilotNumber, session_id: sessionId }),
    },
  );
