/** FIX 166 — human decision board + action selection (human choice only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type HumanDecisionBoardResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_selection_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  autonomous_pr_creation_enabled: boolean;
  autonomous_merge_enabled: boolean;
  autonomous_railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  human_decision_board?: Record<string, unknown>;
  markdown?: string;
};

export type HumanDecisionBoardRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  human_decision_board_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlHumanDecisionBoard = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<HumanDecisionBoardResponse>(
    `/api/v1/mission-control/human-decision-board?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlHumanDecisionBoardRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<HumanDecisionBoardRecordResponse>(`/api/v1/mission-control/human-decision-board/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, kind, content, author }),
  });
