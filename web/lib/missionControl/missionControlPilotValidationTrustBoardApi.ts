/** FIX 183 — pilot validation trust board (validation ≠ re-execution). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PilotValidationTrustBoardResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  direct_execution_performed: boolean;
  direct_provider_mutation_performed: boolean;
  pilot_reexecution_performed: boolean;
  autonomous_validation_execution_enabled: boolean;
  gate_bypass_enabled: boolean;
  governance_mutation_performed: boolean;
  validation_composes_audits_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  pilot_validation_trust_board?: Record<string, unknown>;
  markdown?: string;
};

export type PilotValidationTrustBoardRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  pilot_validation_trust_board_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlPilotValidationTrustBoard = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PilotValidationTrustBoardResponse>(
    `/api/v1/mission-control/pilot-validation-trust-board?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPilotValidationTrustBoardRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<PilotValidationTrustBoardRecordResponse>(
    `/api/v1/mission-control/pilot-validation-trust-board/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
